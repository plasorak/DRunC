#!/usr/bin/env python3
import json

def get_controller_instance(name, port):
    return {
        "name": name,
        "port": port,
        "restriction": "localhost",
        "type": "drunc-controller",
        "configuration": f"file://data/{name}-conf.json",
    }

def get_daq_app_instance(name, port):
    return {
        "name": name,
        "port": port,
        "restriction": "localhost",
        "type": "fake-daq-application",
        "configuration": f"data/{name}-conf.json",
    }


instances = [get_controller_instance(f'topcontroller', 3600)]

import random
random.seed(10)
nsystem = 4

for i in range(nsystem):
    instances.append(get_controller_instance(f'controller{i}', 3601+i))

    napps = random.randint(1,7)
    instances += [get_daq_app_instance(f'app{i}{i2}', 7200+i*1000+i2) for i2 in range(napps)]


executables = {
    "drunc-controller": {
        "executable_and_arguments": [
            {
                "env":[]
            },
            {
                "source": [
                    "${DRUNC_DIR}/setup.sh"
                ]
            },
            {
                "cd" : [
                    "${DRUNC_DIR}"
                ]
            },
            {
                "drunc-controller" : [
                    "${CONFIGURATION}",
                    "${PORT}",
                    "${NAME}"
                ]
            },
            {
                "env":[]
            },
        ],
        "environment": {
            "CONFIGURATION": "{configuration}",
            "DRUNC_DIR": "getenv",
            "NAME": "{name}",
            "PORT": "{port}"
        }
    },
    "fake-daq-application": {
        "executable_and_arguments": [
            {
                "env":[]
            },
            {
                "source": [
                    "${DRUNC_DIR}/setup.sh"
                ]
            },
            {
                "cd" : [
                    "${DRUNC_DIR}"
                ]
            },
            {
                "fake_daq_application" : [
                    "-n", "${NAME}",
                    "-d", "${CONFIGURATION}",
                    "-c", "rest://localhost:${PORT}",
                ]
            },
            {
                "env":[]
            },

        ],
        "environment": {
            "CONFIGURATION": "{configuration}",
            "DRUNC_DIR": "getenv",
            "NAME": "{name}",
            "PORT": "{port}",
        }
    }
}

restrictions = {
    "localhost": {
        "hosts": ["localhost"]
    }
}

boot_data = {
    "instances": instances,
    "executables": executables,
    "restrictions": restrictions,
}

with open('controller-boot-many.json', 'w') as f:
    json.dump(boot_data,f, indent=4)


level0 = ['topcontroller']
level1 = []
level2 = {}

for instance in boot_data['instances']:
    if   'topcontroller' in instance['name']: continue
    elif 'controller'    in instance['name']: level1.append(instance['name'])
    elif 'app'           in instance['name']:
        controller_name = f'controller{instance["name"][3]}'
        if controller_name in level2:
            level2[controller_name].append(instance['name'])
        else:
            level2[controller_name] = [instance['name']]

print(level1)
print(level2)
def generate_conf_data(controller_name:str, children:list[str]) -> None:
    with open(f'{controller_name}-conf.json', 'w') as f:
        json.dump (
            {'children': children},
            f,
            indent=4,
        )


generate_conf_data('topcontroller', level1)

for subcontroller in level1:
    generate_conf_data(subcontroller, level2[subcontroller])

    for app in level2[subcontroller]:
        generate_conf_data(app, {})
