#!/usr/bin/env python3
"""
###############################################################################
# check_mongodb_dbsize.py
# Icinga/Nagios plugin that checks the size of a MongoDB database
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
from subprocess import run, PIPE
from argparse import ArgumentParser
from toml import load


def get_args():
    """ Parse Arguments """
    parser = ArgumentParser(
                 description="Icinga/Nagios plugin which checks the size of a \
                              MongoDB database")
    parser.add_argument("--database", required=True, help="Name of the database",
                        dest="db", type=str)

    threshopts = parser.add_argument_group('Threshold parameters')
    threshopts.add_argument("--wsize", required=False, type=int, dest="wsize",
                            help="Warning threshold for DB size (in Byte)")
    threshopts.add_argument("--csize", required=False, type=int, dest="csize",
                            help="Critical threshold for DB size (in Byte)")
    threshopts.add_argument("--wobj", required=False, type=int, dest="wobj",
                            help="Warning threshold for objects in database")
    threshopts.add_argument("--cobj", required=False, type=int, dest="cobj",
                            help="Critical threshold for objects in database")

    dbopts = parser.add_argument_group('Instance parameters')
    dbopts.add_argument("--credentialfile", required=False,
                        help="Path to credentials file", type=str,
                        dest='credfile', default='/etc/nagios/.mdbservice')
    dbopts.add_argument("--instance", required=False,
                        help="Use credentials for this instance", type=str,
                        dest='instance', default='localhost')

    miscopts = parser.add_argument_group('Miscellaneous options')
    miscopts.add_argument("--mongobin", required=False,
                          help="Location of \"mongo\" binary", type=str, dest='mongoloc',
                          default='/usr/bin/mongo')

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


def convert_bytes_to_pretty(raw_bytes: int):
    """ converts raw bytes into human readable output """
    if raw_bytes >= 1099511627776:
        output = f'{ round(raw_bytes / 1024 **4, 2) }TiB'
    elif raw_bytes >= 1073741824:
        output = f'{ round(raw_bytes / 1024 **3, 2) }GiB'
    elif raw_bytes >= 1048576:
        output = f'{ round(raw_bytes / 1024 **2, 2) }MiB'
    elif raw_bytes >= 1024:
        output = f'{ round(raw_bytes / 1024, 2) }KiB'
    elif raw_bytes < 1024:
        output = f'{ raw_bytes }B'
    return output


def query_db(args, creds: dict):
    """ query instance statistics from MongoDB """

    cmd = [args.mongoloc, f'{ creds["hostname"] }:{ creds["port"] }/{ args.db }',
           "--quiet", "--eval", "JSON.stringify(db.stats())"]

    if creds["user"] != "" and creds["user"] != "":
        # Append parameters for authentification
        cmd.append('-u')
        cmd.append(creds["user"])
        cmd.append('-p')
        cmd.append(creds["pw"])
        cmd.append('--authenticationDatabase')
        cmd.append(creds["authdb"])

    if creds["tls"] is True:
        # Append parameter for TLS connection
        cmd.append('--tls')

    result = run(cmd, shell=False, check=False, stdout=PIPE, stderr=PIPE)

    # Check if command exited without error code
    if result.returncode != 0:
        exit_plugin(3, (f'Error while quering MongoDB: { result.stderr.decode() } \n '
                        f'{ result.stdout.decode() }'), '')

    try:
        for line in result.stdout.decode().splitlines():
            if line.startswith('{"db":'):
                output = json.loads(line)
    except json.decoder.JSONDecodeError as err:
        exit_plugin(3, f'Error while decoding JSON response: { err }', '')

    if 'output' not in locals():
        # No matching JSON line was found in stdout
        exit_plugin(3, 'No valid JSON object found in output!', '')

    return output


def load_db_credentials(file: str, instance: str):
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
    database = {}
    try:
        database['name'] = str(stats['db'])
        database['collections'] = int(stats['collections'])
        database['views'] = int(stats['views'])
        database['objects'] = int(stats['objects'])
        database['indexes'] = int(stats['indexes'])
        database['storage_size'] = int(stats['storageSize'])
        database['index_size'] = int(stats['indexSize'])
        database['data_size'] = int(stats['dataSize'])
        database['total_size'] = int(database['storage_size'] + database['index_size'])

    except KeyError as err:
        exit_plugin(3, f'Error while extracting information from response: {err}', '')

    # Construct output and perfdata strings
    output = (f'Database "{ database["name"] }" contains: '
              f'{ database["collections"] } Collections, '
              f'{ database["views"] } Views, '
              f'{ database["objects"] } Objects, '
              f'{ database["indexes"] } Indexes. '
              f'Size: { convert_bytes_to_pretty(database["total_size"]) }')

    perfdata = (f' | \'collections\'={ database["collections"] };;;; '
                f'\'views\'={ database["views"] };;;; '
                f'\'objects\'={ database["objects"] };{ args.wobj or "" };{ args.cobj or "" };; '
                f'\'indexes\'={ database["indexes"] };;;; '
                f'\'storage_size\'={ database["storage_size"] }B;;;; '
                f'\'data_size\'={ database["data_size"] }B;;;; '
                f'\'total_size\'={ database["total_size"] }B;'
                f'{ args.wsize or "" };{ args.csize or "" };; ')

    # Evaluate status code
    returncode = 0

    if args.wsize is not None and args.wsize <= database['total_size']:
        returncode = 1
    if args.wobj is not None and args.wobj <= database['objects']:
        returncode = 1
    if args.csize is not None and args.csize <= database['total_size']:
        returncode = 2
    if args.cobj is not None and args.cobj <= database['objects']:
        returncode = 2

    exit_plugin(returncode, output, perfdata)


if __name__ == "__main__":
    main()
