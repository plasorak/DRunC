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
```bash
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

## An application has crashed, how do I stop the DAQ?
Let's say the application that has crashed is the `mlt`, which belongs to the `trg-segment`, it is controlled by the `trg-controller`. Status display something like the following:
```
                                           local-1x1-config status
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                   ┃ Info      ┃ State   ┃ Substate ┃ In error ┃ Included ┃ Endpoint                  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ root-controller        │           │ running │ running  │ No       │ Yes      │ grpc://10.73.136.38:46381 │
│   ru-controller        │           │ running │ running  │ No       │ Yes      │ grpc://10.73.136.38:37377 │
│     ru-01              │ conn apa1 │ running │ idle     │ No       │ Yes      │ rest://10.73.136.38:50003 │
│   hsi-fake-controller  │           │ running │ running  │ No       │ Yes      │ grpc://10.73.136.38:46063 │
│     hsi-fake-01        │           │ running │ idle     │ No       │ Yes      │ rest://10.73.136.38:43519 │
│     hsi-fake-to-tc-app │           │ running │ idle     │ No       │ Yes      │ rest://10.73.136.38:57553 │
│   trg-controller       │           │ running │ running  │ No       │ Yes      │ grpc://10.73.136.38:45141 │
│     tc-maker-1         │           │ running │ idle     │ No       │ Yes      │ rest://10.73.136.38:35081 │
│     mlt                │           │ running │ idle     │ Yes      │ Yes      │ rest://10.73.136.38:39393 │
│   df-controller        │           │ running │ running  │ No       │ Yes      │ grpc://10.73.136.38:36513 │
│     tp-stream-writer   │           │ running │ idle     │ No       │ Yes      │ rest://10.73.136.38:37369 │
│     dfo-01             │           │ running │ idle     │ No       │ Yes      │ rest://10.73.136.38:55299 │
│     df-01              │           │ running │ idle     │ No       │ Yes      │ rest://10.73.136.38:54177 │
└────────────────────────┴───────────┴─────────┴──────────┴──────────┴──────────┴───────────────────────────┘
```
In this case, you can do:
```
connect grpc://10.73.136.38:45141 # connect to the trg-controller
exclude # exclude the trg-controller and all of its children
connect grpc://10.73.136.38:46381 # connect to the root-controller
drain-dataflow
stop-trigger-sources
...
```

Note, if it's a controller that has crashed, there is no way to exclude that child from the `root-controller` (so you can `exit` to kill everything).

## So empty...
If you have a question, please reach out to developers or fill an issue [here](https://github.com/DUNE-DAQ/drunc/issues).

