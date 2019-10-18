#!/usr/bin/env python3

from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess
import re
from time import time, sleep
from os import path, environ, getcwd
import sys
import argparse
import yaml
from compose.timeparse import timeparse
# ! FIXME: clean
import docker
from compose.cli.docker_client import docker_client as dc_client
from compose.container import Container
from compose.config import find, load
from compose.project import Project


up_statuses = {"healthy", "up"}
down_statuses = {"down", "unhealthy", "removed"}
stabilized_statuses = up_statuses | down_statuses


def call(command_args):
    return subprocess.run(command_args, check=True, stdout=subprocess.PIPE).stdout.decode()


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


def get_services_container_ids(project):
    #! FIXME: handle no runnng containers!
    services = {
        service.name: next((container.short_id for container in service.containers(stopped=True)), None)
        # ! FIXME: check service id is container name?
        for service in project.services
    }
    return {name: service_id for name, service_id in services.items() if service_id}


def get_services_statuses(service_to_container, all_statuses):
    statuses_by_id = {
        container_id: convert_status(
            next((container_status.status for container_status in all_statuses if container_id.startswith(container_status.id)), "removed")
        )
        for service_name, container_id in service_to_container.items() #! FIXME
    }
    print(statuses_by_id)
    return {
        service_name: statuses_by_id[service_id]
        for service_name, service_id in service_to_container.items()
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
    # ! FIXME: conditional adding to >> "docker-compose.yml"

    docker_client = docker.from_env()
    docker_compose_client = dc_client(environ)
    print(args.file)
    basedir = path.basename(path.dirname(path.abspath(args.file[0])) if args.file else getcwd())
    print(f"BASEDIR   {basedir}")
    project_name = args.project_name or basedir
    print(f"PROJECT   {project_name}")

    config = load(find(basedir, [path.abspath(file) for file in args.file], environ))
    project = Project.from_config(project_name, config, docker_compose_client)
    print(project.services)

    start_time = time()
    timeout = timeparse(args.timeout) if args.timeout is not None else None

    services_ids = get_services_container_ids(project)  # !! FIXME

    while True:
        all_statuses = docker_client.containers.list(all=True) # .status, .id
        # containers = call(["docker", "ps", "--all", "--format", "{{.ID}},{{.Status}}"]).splitlines()
        # # FIXME!  containers(stopped=True) .short_id, human_readable_state/human_readable_health_status

        services_statuses = get_services_statuses(services_ids, all_statuses) # !

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
