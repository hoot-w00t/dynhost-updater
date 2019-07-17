# DynHost Updater
## What is it?
This program is a dynamic DNS client for OVH's DynHost ([https://docs.ovh.com/ie/en/domains/hosting_dynhost/](https://docs.ovh.com/ie/en/domains/hosting_dynhost/)).
It will periodically check for a new IP address and update your (sub)domains when needed.

It uses scripts located in the `scripts` folder to retrieve IP addresses and handle error notifications, that way you can fully adapt it to fit your needs.

## Installation

There are two scripts (`install.sh` and `uninstall.sh`) which will install DynHost as a service on Linux.
It requires Python 3 and the packages inside `requirements.txt` to work.
These commands are aimed at Debian-based distros.

The scripts that come with this repository require `curl` and `sed` to be installed.

```bash
sudo apt update
sudo apt install python3 python3-pip

git clone https://github.com/hoot-w00t/dynhost-updater.git
cd dynhost-updater

python3 -m pip install -U -r requirements.txt

sudo sh install.sh
#sudo sh uninstall.sh
```

To manage the service you can use `sudo systemctl start/stop/status dynhost.service`.
By default the log file will be at `/etc/dynhost/dynhost.log`.

## Configuration

You can take a look at the `examples` and the `scripts` folders to see basic configurations. You can use them as templates.
The program will check its configuration file for any errors before running, you can force a syntax check without starting the program with the `--syntax` parameter. If you need to disable this syntax check, use the `--no-syntax-check` parameter.

### Settings
The settings tell how the program should work.
* `update_delay` is the delay between each check for new IP addresses (in seconds)
* `fallback_ip_method` is the default IP address script to use if the main one fails. (Can be enabled/disabled for each host individually)

The `on_error` block tells the program what to do in case of an error updating a DynHost:
* `enabled` is either `true` or `false` and enables/disables executing a script in case of an error
* `script` is the script name that should be executed when an error occurs

The program will provide the host's name as a parameter to the script.

```json
"update_delay": 300,
"fallback_ip_method": "ipify",

"on_error": {
    "enabled": false,
    "script": "print"
}
```

### Authentication
You can configure multiple credentials to authenticate multiple DynHosts, where:

* `auth1` is the name of the credentials
* `username` is the DynHost username you created (`your_domain.com-suffix`)
* `password` is the associated password

```json
"auth1": {
    "username": "domain.com-suffix",
    "password": "password"
}
```

### Hosts
You can configure as many hosts as you need, where:

* `root` is the name of this host
* `hostname` is the full domain/sub-domain to update
* `auth` is the authentication name to use
* `last_ip` is used by the program to know when it needs to update the DynHost (you can set it to the current IP address it has)
* `ip_method` is the script name to gather the current IP address that this host should have
* `fallback` is either `true` or `false` and enables or disables the use of the fallback IP script if the one you specified doesn't return a valid IP address.

```json
"root": {
    "hostname": "mydomain.com",
    "auth": "default",
    "last_ip": "127.0.0.1",
    "ip_method": "ipify",
    "fallback": true
}
```

### Scripts
Scripts just need to be executable, using `chmod +x your_script_file.sh`.
You can place your scripts inside the existing `scripts` folder before installing with the `install.sh` script. All files inside the folder will be installed and rendered executable.

**Note:** The program expects raw IP addresses such as `127.0.0.1`, you need to take care of the parsing inside the script, otherwise it will not work.

```bash
#!/bin/sh

curl -s something.com/what_is_my_ip
any_other_command
```