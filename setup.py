from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='docker-compose-wait',
    version='1.2.0',
    description='Some useful command line utility to wait until all services declared in a docker-compose file are up and running.',
    long_description=long_description,
    long_description_content_type='text/markdown; charset=UTF-8; variant=GFM',
    url='https://github.com/nicolas-van/docker-compose-wait',
    author='Nicolas Vanhoren',
    classifiers=[
        'Development Status :: 4 - Beta',  # Later: 5 - Production/Stable
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='docker container util',
    py_modules=["docker_compose_wait", "timeparse"],
    install_requires=[
        'PyYAML>=3.12'  # ! TODO: read requirements
    ],
    entry_points={
        'console_scripts': [
            'docker-compose-wait=docker_compose_wait:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/nicolas-van/docker-compose-wait/issues',
        'Source': 'https://github.com/nicolas-van/docker-compose-wait',
    },

    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*',
)
