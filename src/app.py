#!/usr/bin/python
import os.path
import time
import logging
import ConfigParser

from datetime import datetime
from phue import Bridge, Group
from scapy.all import srp,Ether,ARP
from daemon import runner

class App():
    def __init__(self):
        # DaemonRunner config items
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/tmp/phaos.pid'
        self.pidfile_timeout = 5

        # Read the config file
        config = ConfigParser.ConfigParser()
        config.readfp(open('phaos.cfg'))


        # Frequency to poll the devices
        self.poll_interval = config.getfloat('General', 'poll_interval')
        # Hue hostname (reserved IP)
        self.hue_hostname = config.get('Hue', 'bridge_hostname')
        # Group to toggle
        self.group_name = config.get('Hue', 'group_name')
        # Devices to be scanned
        self.devices = config.items('Devices')

        self.log_file = '/var/log/phaos.log'

    def run(self):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            filename=self.log_file,
                            filemode='a')
        while True:
            self.main()
            time.sleep(self.poll_interval)

    def main(self):
        # File used to track number of devices counted in previous run
        device_file = '/serve/phaos/devices.txt'

        # Read the previous count from the file
        if os.path.exists(device_file):
            with open(device_file, 'r') as track_file:
                previous_count = int(track_file.readline())
        else:
            previous_count = 0

        # Arping the devices
        packets = []
        for ip,mac in self.devices:
            ans,unans=srp(Ether(dst=mac)/ARP(pdst=ip),timeout=2,verbose=False)
            # Track the answers
            for pair in ans:
                packets.append(pair)

        current_count = len(packets)

        # Turn on/off the lights given the devices
        logging.info("Previous count: %s - Current count %s", previous_count, current_count)
        if previous_count > 0 and current_count == 0:
            bridge = Bridge(self.hue_hostname)
            Group(bridge, group_name).on = False
        elif previous_count == 0 and current_count > 0:
            bridge = Bridge(self.hue_hostname)
            Group(bridge, group_name).on = True

        # Write current count to file
        with open(device_file, 'w') as track_file:
            track_file.write(str(current_count))


if __name__ == '__main__':
    app = App()
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.do_action()
