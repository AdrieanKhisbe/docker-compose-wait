from setuptools import setup, find_packages
from os import path
import re

HERE = path.abspath(path.dirname(__file__))

with open(path.join(HERE, "README.md"), encoding="utf-8") as readme:
    long_description = readme.read()

with open(path.join(HERE, "requirements.txt")) as requirements:
    install_requires = [dependency for dependency in [
        re.sub(r"\s+#.*$", "", line).strip()
        for line in requirements.read().splitlines()
    ] if dependency]

setup(
    name="docker-compose-wait",
    version="1.2.0",
    description="Some useful command line utility to wait until all services declared in a docker-compose file are up and running.",
    long_description=long_description,
    long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
    url="https://github.com/nicolas-van/docker-compose-wait",
    author="Nicolas Vanhoren",
    classifiers=[
        "Development Status :: 4 - Beta",  # Later: 5 - Production/Stable
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="docker container util",
    packages=["docker_compose_wait"],
    install_requires=install_requires,
    scripts=["bin/docker-compose-wait"],
    project_urls={
        "Bug Reports": "https://github.com/nicolas-van/docker-compose-wait/issues",
        "Source": "https://github.com/nicolas-van/docker-compose-wait",
    },

    python_requires=">=3.6",
)
