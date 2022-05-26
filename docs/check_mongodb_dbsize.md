# check_mongodb_dbsize.py

![Output of check_mongodb_size.py](img/check_mongodb_size_full.png?raw=true "Output of check_mongodb_size.py")

## Usage
```
usage: check_mongodb_dbsize.py [-h] --database DB [--wsize WSIZE] [--csize CSIZE] [--wobj WOBJ] [--cobj COBJ] [--credentialfile CREDFILE] [--instance INSTANCE]
                               [--mongobin MONGOLOC]

Icinga/Nagios plugin which checks the size of a MongoDB database

optional arguments:
  -h, --help            show this help message and exit
  --database DB         Name of the database

Threshold parameters:
  --wsize WSIZE         Warning threshold for DB size (in Byte)
  --csize CSIZE         Critical threshold for DB size (in Byte)
  --wobj WOBJ           Warning threshold for objects in database
  --cobj COBJ           Critical threshold for objects in database

Instance parameters:
  --credentialfile CREDFILE
                        Path to credentials file
  --instance INSTANCE   Use credentials for this instance

Miscellaneous options:
  --mongobin MONGOLOC   Location of "mongo" binary
```

### Usage example
```
./check_mongodb_dbsize.py --database "exampledb"

OK - Database "exampledb" contains: 6 Collections, 0 Views, 8011700 Objects, 19 Indexes. Size: 10.73GiB | 'collections'=6;;;; 'views'=0;;;; 'objects'=8011700;;;; 'indexes'=19;;;; 'storage_size'=10949537792B;;;; 'data_size'=58117632619B;;;; 'total_size'=11526033408B;;;;
```

### Parameters
* `--credentialfile /path/to/.mdbservice` : specify a non-default location for your connection settings file (default: `/etc/nagios/.mdbservice`)
* `--instance server01` : refers to the config section within the `.mdbservice` file (defaults to `localhost`)
* `--mongobin /path/to/mongo` : use this parameter if your `mongo` binary is not located at `/usr/bin/mongo`