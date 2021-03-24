#!/bin/sh

if [ "$(id -u)" -ne 0 ]
    then echo "You need to run this script as root."
    exit
fi

echo "Creating dynhost user..."
useradd --system --shell "$SHELL" --create-home dynhost

echo "Installing Python dependencies for user 'dynhost'..."
su -c "python3 -m pip install --user -r requirements.txt" dynhost

echo "Installing DynHost Updater..."

cp dynhost.py /usr/bin/dynhost
chmod 755 /usr/bin/dynhost

mkdir -p /etc/dynhost/scripts
cp -n examples/dynhost.json.example /etc/dynhost/dynhost.json
cp -rn scripts/* /etc/dynhost/scripts/

chown -R dynhost:dynhost /etc/dynhost/
chmod 640 /etc/dynhost/dynhost.json
chmod 555 /etc/dynhost/scripts/*

mkdir -p /var/log/dynhost/
chown dynhost:dynhost /var/log/dynhost/

echo "Creating service..."

mkdir -p /etc/systemd/system/
cp dynhost.service /etc/systemd/system/dynhost.service

systemctl daemon-reload
systemctl enable dynhost.service

echo "Finished installing!"
