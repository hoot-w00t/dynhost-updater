# DynHost Updater
## What is it?
This program is a dynamic DNS client for OVH's DynHost ([https://docs.ovh.com/ie/en/domains/hosting_dynhost/](https://docs.ovh.com/ie/en/domains/hosting_dynhost/)).
It will periodically check for a new IP address and update your (sub)domains when needed.

It uses scripts located in the `scripts` folder to retrieve IP addresses and handle error notifications, that way you can fully adapt it to fit your needs.

## Installation

There are two scripts (`install.sh` and `uninstall.sh`) which will install DynHost as a Systemd service on Linux.
It requires Python 3.6+ and the packages inside `requirements.txt` to work.

The scripts in the `scripts` folder in this repository require `curl` to be installed.

```bash
# Dependencies for Debian / Raspbian / Ubuntu
sudo apt update
sudo apt install python3 python3-pip git

# Dependencies for Arch / Manjaro
sudo pacman -Syu --needed python python-pip git

# Clone the repository
git clone https://github.com/hoot-w00t/dynhost-updater.git
cd dynhost-updater

# Install
sudo ./install.sh

# Or uninstall
sudo ./uninstall.sh
```

To manage the service you can use `sudo systemctl start/stop/status dynhost.service`.
By default log files will be in `/var/log/dynhost/`.

## Configuration

You can take a look at the `examples` and the `scripts` folders to see basic configurations. You can use them as templates.

The program will check its configuration file for any errors before running, you can force a syntax check without starting the program with the `--syntax` parameter.
If you need to disable this syntax check, for instance if it malfunctions, use the `--no-syntax-check` parameter.

### Settings
The settings tell how the program should work.
* `update_delay` is the delay between each check for changed IP addresses (in seconds)
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
Scripts just need to be executable, using `chmod +x your_script_file.sh` on Linux.

You can place your scripts inside the existing `scripts` folder before installing with the `install.sh` script. All files inside the folder will be installed and rendered executable.

**Note:** The program expects raw IP addresses such as `127.0.0.1`, you need to take care of the parsing inside the script. Any whitespaces will be ignored.

Example for Linux
```bash
#!/bin/sh

curl -s something.com/what_is_my_ip
any_other_command
```

Examples for Windows
```batch
@echo off

curl -s something.com/what_is_my_ip
```
```batch
@curl -s something.com/what_is_my_ip
```

### Logging and arguments
If you need to adjust settings such as logging which are given as arguments to the program you will need to edit the `dynhost.service` file before installing or if you already installed `/etc/systemd/system/dynhost.service`.

If you modify the installed service file you will need to execute `systemctl daemon-reload` and then you can restart the service to apply the changes immediately.

### Note about IPv6
At the time I am writing this, OVH's DynHost only supports IPv4, the program accepts IPv6 addresses returned from scripts but DynHost does not create/update an AAAA field.
