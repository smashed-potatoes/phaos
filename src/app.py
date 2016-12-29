#!/usr/bin/python
import os.path
import time
import datetime
import logging
import ConfigParser


from phue import Bridge, Group, Light
from scapy.all import srp,Ether,ARP
from daemon import runner
from astral import Astral

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
        # Don't mess with casing of config items
        config.optionxform = str
        config.readfp(open('phaos.cfg'))

        # Frequency to poll the devices
        self.poll_interval = config.getfloat('General', 'poll_interval')
        # Hue hostname (reserved IP)
        self.hue_hostname = config.get('General', 'bridge_hostname')
        # Current city
        self.city_name = config.get('General', 'city')

        # Lights to be controlled
        self.lights = config.items('Lights')
        # Groups/rooms to be controlled
        self.groups = config.items('Groups')

        # Devices to be scanned
        self.devices = config.items('Devices')

        self.log_file = '/var/log/phaos.log'

        # Store the city info and set the timezone
        self.city = Astral()[self.city_name]
        os.environ['TZ'] = self.city.timezone

        # Start the count as all devices
        self.count = len(self.devices)


    def run(self):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            filename=self.log_file,
                            filemode='a')

        logging.info("Starting - tracking %s devices", self.count)
        while True:
            self.main()
            time.sleep(self.poll_interval)

    def main(self):

        previous_count = self.count

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
            self.set_lights(False)
        elif previous_count == 0 and current_count > 0:
            self.set_lights(True)

        # Track current count to file
        self.count = current_count

    def set_lights(self, on=True):
        bridge = Bridge(self.hue_hostname)

        # Turn on/off all of the configured lights
        for light,time_config in self.lights:
            # Only change them if the timing info matches
            if self.check_time_config(time_config):
                Light(bridge, light).on = on

        # Turn on/off all of the configured groups
        for group,time_config in self.groups:
            if self.check_time_config(time_config):
                Group(bridge, group).on = on

    def check_time_config(self, config):

        today_sun = self.city.sun(local=True)
        now = datetime.datetime.now(today_sun['dusk'].tzinfo)

        if config.lower() == 'day':
            # After dawn but before dusk
            return now > today_sun['dawn'] and now < today_sun['dusk']
        elif config.lower() == 'night':
            # Before sunrise or after dusk
            return now < today_sun['dawn'] or now > today_sun['dusk']
        elif config.lower() == 'always':
            # Always
            return True
        else:
            # Try to parse config as timespan
            try:
                # Get the from/to time by spliting
                times = config.split('to')
                if len(times) != 2:
                    logging.error('Time frame must be in the format: H:M:S to H:M:S, e.g. 10:00:00 to 17:00:00')
                    return False

                from_time = datetime.datetime.strptime(times[0].strip(), "%H:%M:%S")
                from_time = now.replace(hour=from_time.hour, minute=from_time.minute, second=from_time.second)

                to_time = datetime.datetime.strptime(times[1].strip(), "%H:%M:%S")
                to_time = now.replace(hour=to_time.hour, minute=to_time.minute, second=to_time.second)

                if from_time < to_time:
                    # From time is earlier in the day (during the day)
                    # After from time and before to time
                    return now > from_time and now < to_time
                else:
                    # From time is later in the day (over night)
                    # Before to time or after from time
                    return now < to_time or now > from_time

            except ValueError:
                logging.info("Unknown time config: %s", config)



if __name__ == '__main__':
    app = App()
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.do_action()
