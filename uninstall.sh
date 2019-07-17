#!/bin/sh

if [ $(id -u) -ne 0 ]
  then echo "You need to run this script as root."
  exit
fi

echo "Deleting service..."

systemctl stop dynhost.service
systemctl disable dynhost.service

rm /usr/lib/systemd/system/dynhost.service

deluser --system dynhost

systemctl daemon-reload

echo "Uninstalling DynHost..."

rm /usr/bin/dynhost.py

rm /etc/dynhost/dynhost.json
rm /etc/dynhost/scripts/*

rmdir /etc/dynhost/scripts

echo "Finished uninstalling!"