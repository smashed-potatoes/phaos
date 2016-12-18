#!/usr/bin/env bash
sudo apt-get update
sudo apt-get install -y python

wget https://bootstrap.pypa.io/get-pip.py
sudo -H python get-pip.py

sudo -H pip install scapy
sudo -H pip install phue

sudo mkdir /serve
sudo chown ubuntu:ubuntu /serve/
ln -s /vagrant/src/ /serve/phaos