#!/usr/bin/python3

"""
    Dynamic DNS client for DynHost
    Copyright (C) 2019 akrocynova

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

import os, sys, argparse, time, json, requests

debug = False
do_syntax_check = True
exit_after_syntax_check = False

arg_parser = argparse.ArgumentParser(description="Dynamic DNS Client for DynHost")
arg_parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="Display additional (debug) information")
arg_parser.add_argument("-s", "--syntax", dest="syntax", action="store_true", help="Run a syntax check and exit")
arg_parser.add_argument("-n", "--no-syntax-check", dest="no_syntax_check", action="store_true", help="Disable syntax checking (you may then encounter errors if your configuration has some)")
arg_parser.add_argument("--config", dest="configuration_path", nargs="?", default='dynhost.json', help="Path to the configuration file")
arg_parser.add_argument("--scripts", dest="scripts_path", nargs="?", default='scripts', help="Path to the scripts folder")
arg_parser.add_argument("--log", dest="log_path", nargs="?", default='dynhost.log', help="Path to the log file")
args = arg_parser.parse_args()

debug = args.debug
configuration_file = args.configuration_path
scripts_folder = args.scripts_path
log_file = args.log_path

if args.syntax:
    do_syntax_check = True
    exit_after_syntax_check = True

else:
    if args.no_syntax_check:
        do_syntax_check = False

try:
    log_file_handle = open(log_file, 'a')

except Exception as e:
    print("Error opening the log file: " + str(e))
    sys.exit(1)

def log(obj, is_debug=False):
    if is_debug and not debug : return 1

    line = time.strftime("[%Y-%m-%d %H:%M:%S] ") + str(obj)
    print(line)

    try:
        log_file_handle.write(line + "\n")
        log_file_handle.flush()

    except Exception as e:
        print("Could not write to the log file: " + str(e))

def load_json_file(filename):
    try:
        log("Loading JSON file: " + filename, True)
        with open(filename, 'r') as h:
            return json.load(h)

    except Exception as e:
        log("Error loading JSON file: " + filename + "\n" + str(e))
        return None

def save_json_file(filename, content):
    try:
        log("Saving JSON file: " + filename, True)
        with open(filename, 'w') as h:
            json.dump(content, h, indent=4)
            return True

    except Exception as e:
        log("Error writing JSON file: " + filename + "\n" + str(e))
        return False

def execute_script(script):
    try:
        command = os.path.join(scripts_folder, script)
        log("Executing script: " + command, True)
        return os.popen(command).read()

    except Exception as e:
        log("Error executing script: " + script + "\n" + str(e))
        return None

def check_script(script):
    full_path = os.path.join(scripts_folder, script)
    if os.path.exists(full_path):
        return {"error": False}

    else:
        return {"error": True, "message": "File not found or inaccessible"}

def update_dynhost(host, ip, username, password):
    try:
        log("Updating '" + host + "' with IP " + ip, True)
        req = requests.request(method='GET', url='https://www.ovh.com/nic/update?system=dyndns&hostname=' + host + '&myip=' + str(ip), auth=(username, password))
        if req.status_code == 200:
            return True
        
        elif req.status_code == 401:
            log("Got an HTTP 401 Unauthorized. Check the authentication username and password.")
        
        else:
            log('Unexpected HTTP Response, got HTTP ' + str(req.status_code))
        
        return False

    except Exception as e:
        log('Error while updating DynHost : ' + str(e))
        return False

def get_current_ip(method, fallback=None):
    from_method = execute_script(method)
    if from_method == None or len(from_method) < 1:
        log("Could not retrieve IP address with : " + method)

        if not fallback == None:
            from_fallback = execute_script(fallback)
            if from_fallback == None or len(from_fallback) < 1:
                log("Could not retrieve IP address with fallback method : " + fallback)

            else:
                return from_fallback

    else:
        return from_method

    return None

def check_syntax(config, exit_at_end=False):
    if config == None:
        log("No configuration loaded, exitting.")
        sys.exit(1)

    else:
        if "settings" in config:
            general_settings = [
                "update_delay",
                "fallback_ip_method",
                "on_error",
            ]

            if all(setting in config["settings"] for setting in general_settings):
                try:
                    delay = int(config["settings"]["update_delay"])

                except:
                    log('"update_delay" should be a number, see README.md')
                    sys.exit(3)
                
                fallback_script = check_script(config["settings"]["fallback_ip_method"])
                if fallback_script["error"]:
                    log('"settings" "fallback_ip_method" script error: ' + fallback_script["message"])
                    sys.exit(4)

                on_error_settings = [
                    "enabled",
                    "script",
                ]

                if all(setting in config["settings"]["on_error"] for setting in on_error_settings):
                    if config["settings"]["on_error"]["enabled"]:
                        on_error_script_check = check_script(config["settings"]["on_error"]["script"])
                        if on_error_script_check["error"]:
                            log('"on_error" script error: ' + on_error_script_check["message"])
                            sys.exit(4)

                else:
                    log('"on_error" block is missing one or more settings, see README.md')
                    sys.exit(3)

            else:
                log('"settings" block is missing one or more settings, see README.md')
                sys.exit(2)
        
        else:
            log('"settings" block is missing, see README.md')
            sys.exit(2)
        
        if "auths" in config:
            auth_settings = [
                "username",
                "password",
            ]

            for auth in config["auths"]:
                if not all(setting in config["auths"][auth] for setting in auth_settings):
                    log('Authentication "' + auth + '" is missing one or more settings, see README.md')
                    sys.exit(3)
        
        else:
            log('"auths" block is missing, see README.md')
            sys.exit(2)

        if "hosts" in config:
            host_settings = [
                "hostname",
                "auth",
                "last_ip",
                "ip_method",
                "fallback",
            ]

            for host in config["hosts"]:
                if all(setting in config["hosts"][host] for setting in host_settings):
                    if not config["hosts"][host]["auth"] in config["auths"]:
                        log('Host "' + host + '" points to a missing authentication "' + config["hosts"][host]["auth"] + '"')
                        sys.exit(3)
                    
                    host_script_check = check_script(config["hosts"][host]["ip_method"])
                    if host_script_check["error"]:
                        log('Host "' + host + '" "ip_method" script error: ' + host_script_check["message"])
                        sys.exit(4)
                
                else:
                    log('Host "' + host + '" is missing one or more settings, see README.md')
                    sys.exit(3)

        
        else:
            log('"hosts" block is missing, see README.md')
            sys.exit(2)
        
        if debug or exit_at_end : log("Syntax check: OK")
        if exit_at_end : sys.exit(0)


log("Logging to " + log_file)

configuration = load_json_file(configuration_file)
if do_syntax_check : check_syntax(configuration, exit_after_syntax_check)

log("DynHost Updater started.")
update_delay = int(configuration["settings"]["update_delay"])

while True:
    write_hosts = False

    for host in configuration["hosts"]:
        fallback_method = None
        if configuration["hosts"][host]["fallback"] : fallback_method = configuration["settings"]["fallback_ip_method"]

        current_ip = get_current_ip(configuration["hosts"][host]["ip_method"], fallback_method)
        if current_ip == None:
            log('Skipping "' + configuration["hosts"][host]["hostname"] + '" as no IP address could be retrieved.')

        else:
            if current_ip != configuration["hosts"][host]["last_ip"]:
                # the current ip is different from the last one, we need to update the DNS
                log('Updating "' + configuration["hosts"][host]['hostname'] + '" with ' + current_ip)
                if update_dynhost(configuration["hosts"][host]['hostname'], current_ip, configuration["auths"][configuration["hosts"][host]["auth"]]["username"], configuration["auths"][configuration["hosts"][host]["auth"]]["password"]):
                    configuration["hosts"][host]["last_ip"] = current_ip # remember the new IP because there was no error
                    write_hosts = True

                else:
                    # there was an error
                    if configuration["settings"]["on_error"]["enabled"]:
                        error_script = execute_script(configuration["settings"]["on_error"]["script"] + ' "' + host + '"')
                        log("Error script: " + str(error_script))


    if write_hosts:
        log("Writing hosts after IP change", True)
        save_json_file(configuration_file, configuration)

    log("Waiting " + str(update_delay) + " seconds.", True)
    time.sleep(update_delay)