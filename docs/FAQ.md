# drunc FAQ

## `ServerUnreachable` / `failed to connect to all address`
Note: This has been patched since `v0.11.0`, it is hence recommended that you update the version that you are using if possible.

The connectivity service has statically defined ports, hence you need to check if there are any other `drunc` users on the physical host you are running on. If there are, when you `boot` you will likely get an error of
```
drunc.utils.grpc_utils.ServerUnreachable: ('failed to connect to all addresses; last error: UNKNOWN: ipv4:127.0.0.1:3333: connection attempt timed out before receiving SETTINGS frame', 14)
```
To resolve this issue, the current recommendation is to use a different physical host on which there are no other `drunc` users.

## I am receiving some strange `ssh` errors...
Chances are that you cannot actually ssh onto the named servers. It is recommended that you check whether you can `ssh` onto the servers required by your configuration using `drunc-ssh-validator` as
```
drunc-ssh-validator <configuration_file_with_directory> <session_name>
```
This will tell you which server you cannot `ssh` to.

## What SSH commands are actually run?
The simplest to know how the processes are started is to add the option `--log-level debug` for the process manager shell or the unified shell.

## Do you have unit tests?
Sure,
```bash
cd drunc/
pytest
```
All of the tests are in `tests` and follow the same hierarchy as the code (so for example, the unit tests of the module `drunc.utils.utils` is in `tests/utils/test_utils.py`).

## So empty...
If you have a question, please reach out to developers or fill an issue [here](https://github.com/DUNE-DAQ/drunc/issues).
