#!/usr/bin/python3

import os
from time import sleep

hosts = [ 'www.mydomain.com',
          'sub.mydomain.com'
        ] # the dynhosts you want to update

delay = 120 # delay in seconds between each check for a new IP address

suffix = ''
password = ''

lastWanPath = 'lastWanIp'

lastWanIp = ''
currentIp = ''

if os.path.isfile(lastWanPath): # recover last wan ip after a reboot
    e = open(lastWanPath, 'r')
    lastWanIp = e.read()
    e.close()
    print('Last WAN IP: ' + lastWanIp)
else:
    print('Could not read the last WAN IP, a dynamic update will trigger right away.')

def getCurrentIp():
    command = 'curl -s -X POST -H "Content-Type: application/json" -d \'{"parameters":{}}\' http://192.168.1.254/sysbus/NMC:getWANStatus | sed -e \'s/.*"IPAddress":"\\(.*\\)","Remo.*/\\1/g\''
    return os.popen(command).read()

while True:
    currentIp = getCurrentIp()

    if currentIp != lastWanIp:
        # the current ip is different from the last one, we need to update the DNS
        for host in hosts:
            print('Updating ' + host + ' with ' + currentIp)
            print(os.popen('curl --user "' + suffix + ':' + password + '" "https://www.ovh.com/nic/update?system=dyndns&hostname=' + host + '&myip=' + currentIp + '"').read())

        # write the new ip to lastWan
        g = open(lastWanPath, 'w')
        g.write(currentIp)
        g.close

        lastWanIp = currentIp
    
    sleep(delay)