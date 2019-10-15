#!/bin/bash
set -e

cd /tmp
git clone --branch v0.4.0 https://github.com/sstephenson/bats.git
cd bats
sudo rm -rf /usr/local/bin/bats
(sudo ./install.sh /usr/local)
cd ..
rm -rf bats
bats -h
