#!/usr/bin/env python3
import os
from pathlib import Path
from rich import print

drunc_srcs = (Path(os.path.abspath(__file__)) / ".." / "..").resolve()
test_dir = (Path(os.path.abspath(__file__)) / "..").resolve()
print(f"test_dir {test_dir}")
ignore_prefix_dirs = [drunc_srcs/"apps", drunc_srcs/"tests", drunc_srcs/"data", drunc_srcs/"apps"]
ignore_prefix_dirs = list(map(str, ignore_prefix_dirs))
ignore_dirs = ['__pycache__']

for root, directories, files in os.walk(drunc_srcs):

    ignored_dir = any([ignore_dir in root for ignore_dir in ignore_prefix_dirs])
    ignored_dir |= any([ignore_dir in root for ignore_dir in ignore_dirs])

    if ignored_dir:
        continue
    print(f"Processing {root}")

    for fi in files:
        if not fi.endswith(".py") or fi == '__init__.py':
            continue

        if root == str(drunc_srcs):
            test_root_dir = test_dir
        else:
            test_root_dir = test_dir / root.replace(str(drunc_srcs)+"/", "")

        if not test_root_dir.exists():
            print(f"Creating {test_root_dir}, based on {root}")
            test_root_dir.mkdir(parents=True)
            init_file = test_root_dir/"__init__.py"
            init_file.touch()

        test_file = test_root_dir / f"test_{fi}"

        if not test_file.exists():
            print(f"Creating {test_file}, based on {fi}")
            test_file.touch()

