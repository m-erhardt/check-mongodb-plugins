[![Pylint](https://github.com/m-erhardt/check-mongodb-plugins/actions/workflows/pylint.yml/badge.svg)](https://github.com/m-erhardt/check-mongodb-plugins/actions/workflows/pylint.yml) [![pycodestyle](https://github.com/m-erhardt/check-mongodb-plugins/actions/workflows/pycodestyle.yml/badge.svg)](https://github.com/m-erhardt/check-mongodb-plugins/actions/workflows/pycodestyle.yml) [![Release](https://img.shields.io/github/release/m-erhardt/check-mongodb-plugins.svg)](https://github.com/m-erhardt/check-mongodb-plugins/releases)

# check-mongodb-plugins

![Output of check_mongodb_stats.py](docs/img/check_mongodb_stats.png?raw=true "Output of check_mongodb_stats.py")
![Output of check_mongodb_size.py](docs/img/check_mongodb_size.png?raw=true "Output of check_mongodb_size.py")

## About
* this repository contains a collection of Icinga / Nagios plugins to monitor a MongoDB database
* tested with MongoDB 4.2, 4.4 and 5.0
* Written for python3
* Minimal dependencies (only required non-default library is `toml`)

## Documentation
* [check_mongodb_stats.py](docs/check_mongodb_stats.md)
* [check_mongodb_dbsize.py](docs/check_mongodb_dbsize.md)

## Configuration

#### Python setup
  * Make sure python 3.x is installed on the machine
  * Install `toml` library
    * `pip3 install toml`

#### Configuring the database connection settings
* For security reasons these plugins do not accept the connections parameters for the database as arguments
* Instead the plugins reads the parametes from a hidden toml-formatted configuration file
  * Default: `/etc/nagios/.mdbservice`, use `--credentialfile=/path/to/your/file`for a non-default location
  * Ideally change the file owner and permissions of `.mdbservice` so that only the user executing the plugins can read the config file
    ```toml
    [localhost]
    hostname="localhost"
    port=27017
    user="yourdbuser"
    pw="secretpassword"
    authdb="admin"
    tls=true
    ```

##### Parameters
* `[instancename]` : you can configure multiple connections within one `.mdbservice`-file. This config section name corresponds with the `--instance`-argument of the plugin
* `hostname` : optional, defaults to `localhost`
* `port` : optional, defaults to `27017`
* `user` : optional
* `pw` : optional
* `authdb` : optional, defaults to `admin`
* `tls` : `true`/`false`, defaults to `true`

#### Configuring database use
* Open a MongoDB DB shell, create a dedicated monitoring user and assign the `clusterMonitor` role
  ```java
  use admin
  db.createUser(
      {
          user: "monitoring",
          pwd: passwordPrompt(),
          roles: [
              { role: "clusterMonitor", db: "admin" }
          ]
      }
  )
  ```

