# check_mongodb_stats.py

![Output of check_mongodb_stats.py](img/check_mongodb_stats_full.png?raw=true "Output of check_mongodb_stats.py")

## Usage
```
usage: check_mongodb_stats.py [-h] [--credentialfile CREDFILE] [--instance INSTANCE] [--mongobin MONGOLOC]

Icinga/Nagios plugin which checks metrics of a MongoDB instance

optional arguments:
  -h, --help            show this help message and exit

Instance parameters:
  --credentialfile CREDFILE
                        Path to credentials file
  --instance INSTANCE   Use credentials for this instance

Miscellaneous options:
  --mongobin MONGOLOC   Location of "mongo" binary
```

### Usage example
```
./check_mongodb_stats.py

OK - MongoDB 4.2.20 is up for 15 days, 3:35:10 - Connections: 61, Memory: 7132MiB  | 'conn'=61;;;0;51200 'byte_in'=55427070160B;;;; 'byte_out'=58946125619B;;;; 'transactions'=58946125619;;;; 'mem_virtual'=8710MiB;;;; 'mem_resident'=7132MiB;;;;
```

### Parameters
* `--credentialfile /path/to/.mdbservice` : specify a non-default location for your connection settings file (default: `/etc/nagios/.mdbservice`)
* `--instance server01` : refers to the config section within the `.mdbservice` file (defaults to `localhost`)
* `--mongobin /path/to/mongo` : use this parameter if your `mongo` binary is not located at `/usr/bin/mongo`

