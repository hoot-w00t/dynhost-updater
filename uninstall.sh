#!/bin/sh

if [ "$(id -u)" -ne 0 ]
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

read -rp "Delete DynHost configuration on '/etc/dynhost/' (including scripts)? [y/N] " deleteCfg
case $deleteCfg in
    [yY]* )
        rm -r /etc/dynhost/;
        ;;
    * )
        echo "DynHost configuration will be kept."
        ;;
esac

read -rp "Delete DynHost logs on '/var/log/dynhost/'? [y/N] " deleteLogs
case $deleteLogs in
    [yY]* )
        rm -r /var/log/dynhost/
        ;;
    * )
        echo "DynHost logs will be kept."
        ;;
esac

echo "Finished uninstalling!"