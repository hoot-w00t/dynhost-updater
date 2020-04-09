#!/usr/bin/python3

"""
    Dynamic DNS Client for DynHost
    Copyright (C) 2018-2020 akrocynova

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

licence_header = """\
Dynamic DNS Client for DynHost
Copyright (C) 2018-2020  akrocynova
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions, see the LICENSE file for details.\
"""

from os import path, rename, remove, popen
from argparse import ArgumentParser
from ipaddress import ip_address
from requests import request
from sys import exit, stdout
from time import sleep
import logging
import json
import collections
import pathlib
import typing

class Configuration(collections.UserDict):
    def __init__(self, path: typing.Union[pathlib.Path, str]):
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path).expanduser().resolve()
        self._path = path
        self.load()

    def load(self):
        with self._path.open('r') as h:
            self.data = json.load(h)

    def save(self):
        with self._path.open('w') as h:
            json.dump(self.data, h, indent=4)

def execute_script(script: str, scripts_folder: str):
    try:
        command = path.join(scripts_folder, script)
        logging.debug("Executing script: {}".format(command))
        return popen(command).read().strip()

    except Exception as e:
        logging.error("Error executing script: {}: {}".format(
            script,
            e
            ))
        return None

def update_dynhost(host: str, ip: str, username: str, password: str):
    req = request(
        method="GET",
        url="https://www.ovh.com/nic/update?system=dyndns&hostname={}&myip={}".format(host, ip),
        auth=(username, password)
        )

    if req.status_code == 200:
        logging.warning("Updated \"{}\" with IP \"{}\"".format(host, ip))

    elif req.status_code == 401:
        raise Exception("Authentication failed for \"{}\", verify the credentials".format(host))

    else:
        raise Exception("Updated failed for \"{}\", got unexpected status code {}".format(
                            host,
                            req.status_code,
                        ))

def is_valid_ip(ip: str):
    try:
        ip_address(ip)
        return True

    except:
        return False

def get_current_ip(method: str, scripts_folder: str, fallback: str = None):
    from_method = execute_script(method, scripts_folder)
    if is_valid_ip(from_method):
        return from_method

    else:
        logging.warning("Could not retrieve valid IP address using: {}".format(method))

        if fallback != None:
            from_fallback = execute_script(fallback, scripts_folder)
            if is_valid_ip(from_fallback):
                return from_fallback

            else:
                logging.error("Could not retrieve valid IP address using fallback method: {}".format(fallback))

    return None

def check_script(script: str, scripts_folder: str):
    full_path = path.join(scripts_folder, script)
    if path.exists(full_path):
        return {"error": False}

    else:
        return {"error": True, "message": "File not found or inaccessible"}

def check_syntax(config: dict, scripts_folder: str):
    if "settings" in config:
        general_settings = [
            "update_delay",
            "fallback_ip_method",
            "on_error",
        ]

        if all(setting in config["settings"] for setting in general_settings):
            try:
                int(config["settings"]["update_delay"])

            except:
                logging.error('"update_delay" should be a number, see README.md')
                return False

            fallback_script = check_script(config["settings"]["fallback_ip_method"], scripts_folder)
            if fallback_script["error"]:
                logging.error('"settings" -> "fallback_ip_method": script error: {}'.format(
                    fallback_script["message"]
                    ))
                return False

            on_error_settings = [
                "enabled",
                "script",
            ]

            if all(setting in config["settings"]["on_error"] for setting in on_error_settings):
                if config["settings"]["on_error"]["enabled"]:
                    on_error_script_check = check_script(config["settings"]["on_error"]["script"], scripts_folder)
                    if on_error_script_check["error"]:
                        logging.error('"on_error": script error: {}'.format(
                            on_error_script_check["message"]
                        ))
                        return False

            else:
                logging.error('"on_error" block is missing one or more settings, see README.md')
                return False

        else:
            logging.error('"settings" block is missing one or more settings, see README.md')
            return False

    else:
        logging.error('"settings" block is missing, see README.md')
        return False

    if "auths" in config:
        auth_settings = [
            "username",
            "password",
        ]

        for auth in config["auths"]:
            if not all(setting in config["auths"][auth] for setting in auth_settings):
                logging.error('Authentication "{}" is missing one or more settings, see README.md'.format(
                    auth
                ))
                return False

    else:
        logging.error('"auths" block is missing, see README.md')
        return False

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
                    logging.error('Host "{}" points to a missing authentication "{}"'.format(
                        host,
                        config["hosts"][host]["auth"]
                        ))
                    return False

                host_script_check = check_script(
                    config["hosts"][host]["ip_method"],
                    scripts_folder
                    )
                if host_script_check["error"]:
                    logging.error('Host "{}" -> "ip_method": script error: {}'.format(
                        host,
                        host_script_check["message"]
                        ))
                    return False

            else:
                logging.error('Host "{}" is missing one or more settings, see README.md'.format(
                    host
                ))
                return False


    else:
        logging.error('"hosts" block is missing, see README.md')
        return False

    return True

if __name__ == "__main__":
    print(licence_header)

    arg_parser = ArgumentParser(description="Dynamic DNS Client for DynHost")
    arg_parser.add_argument(
        "-s", "--syntax",
        dest="syntax",
        action="store_true",
        help="Run a syntax check and exit"
        )
    arg_parser.add_argument(
        "-n", "--no-syntax-check",
        dest="no_syntax_check",
        action="store_true",
        help="Disable syntax verification (you may then encounter errors if your configuration has some)"
        )
    arg_parser.add_argument(
        "-c", "--config",
        dest="configuration_file",
        type=str,
        default="dynhost.json",
        help="Path to the configuration file"
        )
    arg_parser.add_argument(
        "--scripts",
        dest="scripts_folder",
        type=str,
        default="scripts",
        help="Path to the scripts folder"
        )
    arg_parser.add_argument(
        "--loglevel",
        dest="loglevel",
        type=str,
        default=None,
        help="Logging level (default: warning)"
        )
    arg_parser.add_argument(
        "--logfile",
        dest="logfile",
        type=str,
        default=None,
        help="Save log output to this file"
        )
    arg_parser.add_argument(
        "--rotate-log",
        dest="rotate_log",
        action="store_true",
        help="Perform a log rotation on startup"
        )
    arg_parser.add_argument(
        "--max-rotations",
        dest="max_rotations",
        type=int,
        default=5,
        help="How many old log files to keep (default: 5, 0: keep all)"
        )
    args = arg_parser.parse_args()

    logging_levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG
        }

    if args.loglevel == None:
        logging_level = logging.WARNING

    else:
        logging_level = logging_levels.get(
            args.loglevel.strip().lower(),
            None
            )

        if logging_level == None:
            print("Incorrect logging level: \"{}\"".format(args.loglevel))
            exit(1)

    try:
        logformat = logging.Formatter("[%(levelname)s] [%(asctime)s] %(message)s")
        logger = logging.getLogger()
        logger.setLevel(logging_level)

        logstdout_h = logging.StreamHandler(stream=stdout)
        logstdout_h.setFormatter(logformat)
        logger.addHandler(logstdout_h)

        if args.logfile != None:
            full_rotation = False
            log_rotated = False
            if args.rotate_log and path.exists(args.logfile):
                if args.max_rotations == 1:
                    remove("{}.1".format(args.logfile))
                    full_rotation = True

                elif path.exists("{}.{}".format(args.logfile, args.max_rotations)) and args.max_rotations > 1:
                    for r in range(2, args.max_rotations + 1):
                        rename("{}.{}".format(args.logfile, r), "{}.{}".format(args.logfile, r - 1))
                    full_rotation = True

                ro_log_index = 1
                ro_logfile = "{}.{}".format(args.logfile, ro_log_index)
                while path.exists(ro_logfile):
                    ro_log_index += 1
                    ro_logfile = "{}.{}".format(args.logfile, ro_log_index)
                rename(args.logfile, ro_logfile)
                log_rotated = True

            logfile_h = logging.FileHandler(filename=args.logfile)
            logfile_h.setFormatter(logformat)
            logger.addHandler(logfile_h)

            if full_rotation:
                logging.info("Old log files have rotated")

            if log_rotated:
                logging.info("Last log file moved to {}".format(
                    ro_logfile
                ))

    except Exception as e:
        print("Could not setup logging: {}".format(str(e)))
        exit(1)

    try:
        configuration = Configuration(args.configuration_file)

    except Exception as e:
        logging.critical("Could not load configuration: {}".format(e))
        exit(1)

    if args.syntax:
        if check_syntax(configuration, args.scripts_folder):
            print("Syntax check: OK")
            exit(0)
        else:
            exit(2)

    elif not args.no_syntax_check:
        if not check_syntax(configuration, args.scripts_folder):
            exit(2)

    logging.info("DynHost Updater started")
    update_delay = int(configuration["settings"]["update_delay"])

    while True:
        write_hosts = False

        for host in configuration["hosts"]:
            fallback_method = configuration["settings"]["fallback_ip_method"] if configuration["hosts"][host]["fallback"] else None

            current_ip = get_current_ip(
                configuration["hosts"][host]["ip_method"],
                args.scripts_folder,
                fallback=fallback_method
                )

            if current_ip == None:
                logging.error("Skipping \"{}\" as no valid IP address could be retrieved".format(
                    configuration["hosts"][host]["hostname"]
                ))

            elif current_ip != configuration["hosts"][host]["last_ip"]:
                logging.info("Updating \"{}\" with IP \"{}\"".format(
                    configuration["hosts"][host]['hostname'],
                    current_ip
                    ))

                try:
                    update_dynhost(
                        configuration["hosts"][host]['hostname'],
                        current_ip,
                        configuration["auths"][configuration["hosts"][host]["auth"]]["username"],
                        configuration["auths"][configuration["hosts"][host]["auth"]]["password"]
                        )

                    configuration["hosts"][host]["last_ip"] = current_ip
                    write_hosts = True

                except Exception as e:
                    logging.critical("Error encountered while updating {}: {}".format(
                        host,
                        e,
                    ))
                    if configuration["settings"]["on_error"]["enabled"]:
                        error_script = execute_script(
                            "{} \"{}\"".format(
                                configuration["settings"]["on_error"]["script"],
                                host),
                            args.scripts_folder
                            )

        if write_hosts:
            logging.debug("Writing hosts after IP change")
            try:
                configuration.save()

            except Exception as e:
                logging.error("Could not save configuration file: {}".format(e))

        logging.debug("Waiting {} seconds".format(update_delay))
        sleep(update_delay)