#!/bin/sh

if [ $(id -u) -ne 0 ]
  then echo "You need to run this script as root."
  exit
fi

echo "Deleting service..."

systemctl stop dynhost.service
systemctl disable dynhost.service

rm /etc/systemd/system/dynhost.service

userdel --remove --force dynhost

systemctl daemon-reload

echo "Uninstalling DynHost..."

rm /usr/bin/dynhost
rm -r /etc/dynhost
rm -r /var/log/dynhost

echo "Finished uninstalling!"