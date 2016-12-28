#!/usr/bin/python

import os.path

from datetime import datetime
from phue import Bridge, Group
from scapy.all import srp,Ether,ARP
import time
from daemon import runner

class App():
	def __init__(self):
        	self.stdin_path = '/dev/null'
       	 	self.stdout_path = '/dev/tty'
        	self.stderr_path = '/dev/tty'
        	self.pidfile_path =  '/tmp/foo.pid11'
        	self.pidfile_timeout = 5

    	def run(self):
        	while True:
			self.main()
            		time.sleep(111)

	def main(self):
		"""===  Configuration ==="""
    		# MAC and IPs to check for
    		# IPs are set as reserved in router to avoid changes
    		to_scan = {
        		'D8:C4:6A:23:B4:05': '192.168.0.15/32',
        		'60:F1:89:1B:F6:E4': '192.168.0.16/32'
    		}
    		# Group to toggle
    		group_name = 'Main Room'
    		# Hue hostname (also reserved IP)
 		hostname = '192.168.0.11'
    		device_file = '/serve/phaos/devices.txt'

    		# Read the previous count from the file
    		if os.path.exists(device_file):
        		with open(device_file, 'r') as track_file:
            			previous_count = int(track_file.readline())
    		else:
        		previous_count = 0

    		# Arping the devices
    		packets = []
    		for mac,ip in to_scan.iteritems():
        		ans,unans=srp(Ether(dst=mac)/ARP(pdst=ip),timeout=2)
        		# Track the answers
        		for pair in ans:
            			packets.append(pair)

    		current_count = len(packets)

    		# Turn on/off the lights given the devices
    		print str(datetime.now()), "Previous count:", previous_count, "Current count:", current_count
    		if previous_count > 0 and current_count == 0:
        		bridge = Bridge(hostname)
        		Group(bridge, group_name).on = False
    		elif previous_count == 0 and current_count > 0:
        		bridge = Bridge(hostname)
        		Group(bridge, group_name).on = True

    		# Write current count to file
    		with open(device_file, 'w') as track_file:
        		track_file.write(str(current_count))


app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()

#Note that you'll need the python-deaemon library. In Ubuntu, you would:
#sudo apt-get install python-daemon
#Then just start it with ./howdy.py start, and stop it with ./howdy.py stop.
