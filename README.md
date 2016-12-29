# Phaos
Phaos is a script that turns on and off a group of Philips Hue lights based on certain devices being connected to the same network (i.e. mobile phones).

The reason it has been created is so that the lights only turn off when all people have left the home and turn on when at least one has returned.

# Requirements
The following can be installed using pip: `pip install [package]`
- scapy
- phue
- python-daemon

# Setup
1. Make sure the script is executable with `chmod +x app.py`
2. Set your mobile devices to have reserved/static IP assignments
3. Set the following variables in `app.py`:
    - `to_scan`:  Your mobile devices' MAC and IP addresses
    - `hostname`: The hostname/IP of your Hue Bridge
    - `group_name`: The name of the room/group that you would like to turn on/off

# Usage
Before running the daemon for the first time, press the button on top if your hue hub, this allows it to get an auth token.
This only needs to be done the first time, it stores the hue token in ~/.python_hue

The daemon can be started, stopped or restarted by calling the script with the appropriate command:
`sudo ./app.py start|stop|restart`

Note: The daemon must be run with sudo to allow for access to the socket for the ARP ping