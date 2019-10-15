#!/usr/bin/env python3

from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess
import re
import time
import sys
import argparse
import yaml
from compose.timeparse import timeparse

up_statuses = {"healthy", "up"}
down_statuses = {"down", "unhealthy", "removed"}
stabilized_statuses = up_statuses | down_statuses

def call(args):
    return "\n".join(
        subprocess.check_output(args).decode().splitlines()  # ! FIXME: check
    )

def get_all_statuses():
    containers = call(["docker", "ps", "--all", "--format", "{{.ID}},{{.Status}}"]).splitlines()
    return [container.split(",") for container in containers]

def get_statuses_for_ids(container_ids):
    status_list = get_all_statuses()
    return {
        container_id: next((c_status for [c_id, c_status] in status_list if container_id.startswith(c_id)), "removed")
        for container_id in container_ids
    }

def convert_status(status):
    res = re.search(r"^([^\s]+)[^\(]*(?:\((.*)\).*)?$", status)
    if res is None:
        raise Exception(f"Unknown status format {status}")

    if res.group(1) != "Up":
        return "down"

    if res.group(2) == "health: starting":  #! TO DICT
        return "starting"
    elif res.group(2) == "healthy":
        return "healthy"  #! FIXME
    elif res.group(2) == "unhealthy":
        return "unhealthy"
    elif res.group(2) is None:
        return "up"
    else:
        raise Exception(f"Unknown status format {status}")

def get_converted_statuses(container_ids):
    return {
        container_id: convert_status(status)
        for container_id, status in get_statuses_for_ids(container_ids).items()
    }

def get_docker_compose_args(args):
    nargs = []
    for f in args.file:
        nargs += ["-f", f]
    if args.project_name:
        nargs += ["-p", args.project_name]
    return nargs

def get_services_ids(dc_args):
    services_names = yaml.load(call(["docker-compose", *dc_args, "config"]))["services"].keys()
    services = {}
    for name in services_names:
        service_id = call(["docker-compose", *dc_args, "ps", "-q", name]).strip()
        if service_id != "":
            services[name] = service_id
    return services

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
    parser.add_argument("-f", "--file", action="append", default=[],
                    help="Specify an alternate compose file (default: docker-compose.yml)")
    parser.add_argument("-p", "--project-name",
                    help="Specify an alternate project name (default: directory name)")
    parser.add_argument("-w", "--wait", action="store_true",
                    help="Wait for all the processes to stabilize before exit (default behavior is to exit "
                    + "as soon as any of the processes is unhealthy)")
    parser.add_argument("-t", "--timeout", default=None,
                    help="Max amount of time during which this command will run (expressed using the "
                    + "same format than in docker-compose.yml files, example: 5s, 10m,... ). If there is a "
                    + "timeout this command will exit returning 1. (default: wait for an infinite amount of time)")

    args = parser.parse_args()
    dc_args = get_docker_compose_args(args)

    start_time = time.time()
    timeout = timeparse(args.timeout) if args.timeout is not None else None

    services_ids = get_services_ids(dc_args)

    while True:
        statuses = get_services_statuses(services_ids)

        if args.wait:
            if any([v not in stabilized_statuses for k, v in statuses.items()]):
                continue

        if all([v in up_statuses for k, v in statuses.items()]):
            print("All processes up and running")
            exit(0)
        elif any([v in down_statuses for k, v in statuses.items()]):
            print("Some processes failed:")
            for k, v in [(k, v) for k, v in statuses.items() if v in down_statuses]:
                print("%s is %s" % (k, v))
            exit(-1)

        if args.timeout is not None and time.time() > start_time + timeout:
            print("Timeout")
            exit(1)

        time.sleep(1)

if __name__ == "__main__":
    # execute only if run as a script
    main()
