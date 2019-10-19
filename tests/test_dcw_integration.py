from subprocess import run, PIPE
from os import path

DCW_MAIN = path.join(path.dirname(__file__), "..", "docker_compose_wait.py")

def dc_file(name):
    return path.join(path.dirname(__file__), "dockerfiles", f"docker-compose-{name}.yml")

def run_launch_dc_and_wait(dc_file, *extra_flags):
    run(["docker-compose", "-f", dc_file, "up", "-d"], stdout=PIPE, stderr=PIPE)
    return run(
        ["python", DCW_MAIN, "-f", dc_file, *extra_flags],
        stdout=PIPE, stderr=PIPE  # capture_output only supported from 3.7
    )

def run_dc_down(dc_file):
    run(["docker-compose", "-f", dc_file, "down"], stdout=PIPE, stderr=PIPE)

def test_simple():
    execution_status = run_launch_dc_and_wait(dc_file("simple"))
    run_dc_down(dc_file("simple"))
    assert execution_status.returncode is 0

def test_fail():
    execution_status = run_launch_dc_and_wait(dc_file("fail"))
    run_dc_down(dc_file("fail"))
    assert execution_status.returncode is 255


def test_no_healthcheck():
    execution_status = run_launch_dc_and_wait(dc_file("no-healthcheck"))
    run_dc_down(dc_file("no-healthcheck"))
    assert execution_status.returncode is 0


def test_down():
    execution_status = run_launch_dc_and_wait(dc_file("down"))
    run_dc_down(dc_file("down"))
    assert execution_status.returncode is 255


def test_twodotone():
    execution_status = run_launch_dc_and_wait(dc_file("2.1"))
    run_dc_down(dc_file("2.1"))
    assert execution_status.returncode is 0


def test_no_wait():
    execution_status = run_launch_dc_and_wait(dc_file("wait"))
    run_dc_down(dc_file("wait"))
    assert execution_status.returncode is 255
    output = str(execution_status.stdout)
    assert "Some processes failed:" in output
    assert "test1 is unhealthy" in output
    assert "test2" not in output


def test_wait():
    execution_status = run_launch_dc_and_wait(dc_file("wait"), "-w")
    run_dc_down(dc_file("wait"))
    assert execution_status.returncode is 255
    output = str(execution_status.stdout)
    assert "test1 is unhealthy" in output
    assert "test2 is unhealthy" in output


def test_timeout():
    execution_status = run_launch_dc_and_wait(dc_file("wait"), "-t", "2s")
    run_dc_down(dc_file("timeout"))
    assert execution_status.returncode is 1
