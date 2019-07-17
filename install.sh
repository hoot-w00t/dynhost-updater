#!/bin/sh

if [ $(id -u) -ne 0 ]
  then echo "You need to run this script as root."
  exit
fi

echo "Installing DynHost..."

adduser --system --shell /bin/bash --group --disabled-password --no-create-home dynhost

cp dynhost.py /usr/bin/dynhost.py
chmod 755 /usr/bin/dynhost.py

mkdir -p /etc/dynhost/

cp examples/dynhost.json.example /etc/dynhost/dynhost.json

cp -r scripts/ /etc/dynhost/scripts

chown -R dynhost:dynhost /etc/dynhost/

chmod 640 /etc/dynhost/dynhost.json
chmod 555 /etc/dynhost/scripts/*

echo "Creating service..."

mkdir -p /usr/lib/systemd/system/

cp dynhost.service /usr/lib/systemd/system/dynhost.service

systemctl daemon-reload
systemctl enable dynhost.service

echo "Finished installing!"