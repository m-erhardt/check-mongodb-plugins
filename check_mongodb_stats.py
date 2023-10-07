#!/usr/bin/env python3
"""
###############################################################################
# check_mongodb_stats.py
# Icinga/Nagios plugin that checks metrics of a MongoDB instance
#
# Author        : Mauno Erhardt <mauno.erhardt@burkert.com>
# Copyright     : (c) 2022 Burkert Fluid Control Systems
# Source        : https://github.com/m-erhardt/check-mongodb-plugins
# License       : GPLv3 (http://www.gnu.org/licenses/gpl-3.0.txt)
#
###############################################################################
"""

import sys
import json
from datetime import timedelta
from subprocess import run, PIPE
from argparse import ArgumentParser, Namespace as Arguments
from toml import load


def get_args() -> Arguments:
    """ Parse Arguments """
    parser = ArgumentParser(
                 description="Icinga/Nagios plugin which checks metrics of a \
                              MongoDB instance")
    dbopts = parser.add_argument_group('Instance parameters')
    dbopts.add_argument("--credentialfile", required=False,
                        help="Path to credentials file", type=str,
                        dest='credfile', default='/etc/nagios/.mdbservice')
    dbopts.add_argument("--instance", required=False,
                        help="Use credentials for this instance", type=str,
                        dest='instance', default='localhost')
    miscopts = parser.add_argument_group('Miscellaneous options')
    miscopts.add_argument("--mongobin", required=False,
                          help="Location of \"mongosh\" binary", type=str, dest='mongoloc',
                          default='/usr/bin/mongosh')

    args = parser.parse_args()
    return args


def exit_plugin(returncode: int, output: str, perfdata: str):
    """ Check status and exit accordingly """
    if returncode == 3:
        print("UNKNOWN - " + str(output))
        sys.exit(3)
    if returncode == 2:
        print("CRITICAL - " + str(output) + str(perfdata))
        sys.exit(2)
    if returncode == 1:
        print("WARNING - " + str(output) + str(perfdata))
        sys.exit(1)
    elif returncode == 0:
        print("OK - " + str(output) + str(perfdata))
        sys.exit(0)


def query_db(args, creds: dict) -> dict:
    """ query instance statistics from MongoDB """

    cmd = [args.mongoloc, f'{ creds["hostname"] }:{ creds["port"] }',
           "--quiet", "--eval", "EJSON.stringify(db.serverStatus())"]

    if creds["user"] != "" and creds["pw"] != "":
        # Append parameters for authentification
        cmd.append('-u')
        cmd.append(creds["user"])
        cmd.append('-p')
        cmd.append(creds["pw"])
        cmd.append('--authenticationDatabase')
        cmd.append(creds["authdb"])

    # Append parameter for TLS connection
    if creds["tls"] is True:
        cmd.append('--tls')

    if creds.get("tlscafile") is not None:
        cmd.append('--tlsCAFile')
        cmd.append(f'{ creds["tlscafile"] }')

    if creds["tls_allow_invalid_hostnames"] is True and creds["tls"] is True:
        cmd.append('--tlsAllowInvalidHostnames')

    if creds["tls_allow_invalid_certificates"] is True and creds["tls"] is True:
        cmd.append('--tlsAllowInvalidCertificates')

    result = run(cmd, shell=False, check=False, stdout=PIPE, stderr=PIPE)

    # Check if command exited without error code
    if result.returncode != 0:
        exit_plugin(3, (f'Error while quering MongoDB: { result.stderr.decode() } \n '
                        f'{ result.stdout.decode() }'), '')

    try:
        for line in result.stdout.decode().splitlines():
            if line.startswith('{"host":'):
                output = json.loads(line)
    except json.decoder.JSONDecodeError as err:
        exit_plugin(3, f'Error while decoding JSON response: { err }', '')

    return output


def load_db_credentials(file: str, instance: str) -> dict:
    """ load MongoDB credentials from file """

    try:
        # load toml/ini config into dict
        config = load(file)
    except FileNotFoundError:
        exit_plugin(3, f'Credential file { file } not found!', '')

    try:
        creds = config[instance]
    except KeyError:
        exit_plugin(3, f'Instance { instance } not found in credential file { file }!', '')

    # Set default options if not set in ini file
    if creds.get("hostname") is None:
        creds["hostname"] = "localhost"
    if creds.get("port") is None:
        creds["port"] = 27017
    if creds.get("user") is None:
        creds["user"] = ""
    if creds.get("pw") is None:
        creds["pw"] = ""
    if creds.get("authdb") is None:
        creds["authdb"] = "admin"
    if creds.get("tls") is None:
        creds["tls"] = True
    if creds.get("tls_allow_invalid_hostnames") is None:
        creds["tls_allow_invalid_hostnames"] = False
    if creds.get("tls_allow_invalid_certificates") is None:
        creds["tls_allow_invalid_certificates"] = False

    return creds


def main():
    """ Main program code """

    # Get Arguments
    args = get_args()

    # Load DB credentials from file
    creds = load_db_credentials(args.credfile, args.instance)

    # Query MongoDB
    stats = query_db(args, creds)

    # Extract system information from API response
    instance = {}
    try:
        instance['version'] = str(stats['version'])
        instance['uptime'] = int(stats['uptime'])
        instance['uptime_str'] = str(timedelta(seconds=instance["uptime"]))
        instance['state'] = int(stats['ok'])
        instance['conn_cur'] = int(stats['connections']['current'])
        instance['conn_avail'] = int(stats['connections']['available'])
        instance['conn_total'] = int(instance['conn_cur'] + instance['conn_avail'])
        instance['byte_in'] = int(stats['network']['bytesIn'])
        instance['byte_out'] = int(stats['network']['bytesOut'])
        instance['transactions'] = int(stats['transactions']['totalCommitted'])
        instance['mem_virt'] = int(stats['mem']['virtual'])
        instance['mem_resident'] = int(stats['mem']['resident'])

    except KeyError as err:
        exit_plugin(3, f'Error while extracting information from response: {err}', '')

    # Construct output and perfdata strings
    output = (f'MongoDB { instance["version"] } is up for '
              f'{ instance["uptime_str"] } '
              f'- Connections: { instance["conn_cur"] }, '
              f'Memory: { instance["mem_resident"] }MiB ')

    perfdata = (f' | \'conn\'={ instance["conn_cur"] };;;0;{ instance["conn_total"] } '
                f'\'byte_in\'={ instance["byte_in"] }B;;;; '
                f'\'byte_out\'={ instance["byte_out"] }B;;;; '
                f'\'transactions\'={ instance["byte_out"] };;;; '
                f'\'mem_virtual\'={ instance["mem_virt"] }MiB;;;; '
                f'\'mem_resident\'={ instance["mem_resident"] }MiB;;;; ')

    if instance['state'] == 1:
        exit_plugin(0, output, perfdata)
    else:
        exit_plugin(1, output, perfdata)


if __name__ == "__main__":
    main()
