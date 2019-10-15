#!/usr/bin/env python3

from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess
import re
from time import time, sleep
import sys
import argparse
import yaml
from compose.timeparse import timeparse

up_statuses = {"healthy", "up"}
down_statuses = {"down", "unhealthy", "removed"}
stabilized_statuses = up_statuses | down_statuses

def call(command_args):
    return subprocess.run(command_args, check=True, stdout=subprocess.PIPE).stdout.decode()

def get_all_statuses():
    containers = call(["docker", "ps", "--all", "--format", "{{.ID}},{{.Status}}"]).splitlines()
    return [container.split(",") for container in containers]

def get_statuses_for_ids(container_ids):
    status_list = get_all_statuses()
    return {
        container_id: next((c_status for [c_id, c_status] in status_list if container_id.startswith(c_id)), "removed")
        for container_id in container_ids
    }

NORMALIZED_STATUSES = {
    "health: starting": "starting",
    "healthy": "healthy",
    "unhealthy": "unhealthy",
    None: "up"
}

def convert_status(status):
    match = re.search(r"^([^\s]+)[^\(]*(?:\((.*)\).*)?$", status)
    if not match:
        raise Exception(f"Unknown status format {status}")

    if match.group(1) != "Up":
        return "down"

    try:
        return NORMALIZED_STATUSES[match.group(2)]
    except KeyError:
        raise Exception(f"Unknown status format {status}")

def get_converted_statuses(container_ids):
    return {
        container_id: convert_status(status)
        for container_id, status in get_statuses_for_ids(container_ids).items()
    }

def get_docker_compose_args(args):
    dc_file_args = [arg for arg_list in [["-f", file] for file in args.file] for arg in arg_list]
    dc_project_args = ["-p", args.project_name] if args.project_name else []
    return dc_file_args + dc_project_args

def get_services_ids(dc_args):
    services = {
        name: call(["docker-compose", *dc_args, "ps", "-q", name]).strip()
        for name in yaml.load(call(["docker-compose", *dc_args, "config"]))["services"].keys()
    }
    return {name: service_id for name, service_id in services.items() if service_id}

def get_services_statuses(services_with_ids):
    statuses_by_id = get_converted_statuses(services_with_ids.values())
    return {
        service_name: statuses_by_id[service_id]
        for service_name, service_id in services_with_ids.items()
    }

def main():
    parser = argparse.ArgumentParser(
        description="Wait until all services in a docker-compose file are healthy. Options are forwarded to docker-compose.",
        usage="docker-compose-wait.py [options]"
    )
    parser.add_argument(
        "-f", "--file", action="append", default=[],
        help="Specify an alternate compose file (default: docker-compose.yml)"
    )
    parser.add_argument(
        "-p", "--project-name",
        help="Specify an alternate project name (default: directory name)"
    )
    parser.add_argument(
        "-w", "--wait", action="store_true",
        help="Wait for all the processes to stabilize before exit (default behavior is to exit as soon as any of the processes is unhealthy)"
    )
    parser.add_argument("-t", "--timeout", default=None,
        help="Max amount of time during which this command will run (expressed using the same format than in docker-compose.yml files, "
        "example: 5s, 10m,... ). If there is a timeout this command will exit returning 1. (default: wait for an infinite amount of time)"
    )

    args = parser.parse_args()
    dc_args = get_docker_compose_args(args)

    start_time = time()
    timeout = timeparse(args.timeout) if args.timeout is not None else None

    services_ids = get_services_ids(dc_args)

    while True:
        services_statuses = get_services_statuses(services_ids)

        if args.wait and any([status not in stabilized_statuses for service, status in services_statuses.items()]):
            continue

        if all([status in up_statuses for service, status in services_statuses.items()]):
            print("All processes up and running")
            sys.exit(0)

        down_services_statuses = {service: status for service, status in services_statuses.items() if status in down_statuses}
        if down_services_statuses:
            print("Some processes failed:")
            for service, status in down_services_statuses.items():
                print(f"{service} is {status}")
            sys.exit(-1)

        if args.timeout is not None and time() > start_time + timeout:
            print("Timeout")
            sys.exit(1)

        sleep(1)

if __name__ == "__main__":
    main()
