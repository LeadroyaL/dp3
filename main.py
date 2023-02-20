#!/usr/bin/env python3

import os
import sys
import importlib
import logging
from typing import List

from dp3_plugin import Dp3Plugin

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-5.5s] %(module)s %(message)s")

plugin_info = dict()
plugin_info["apk_merge"] = "ApkMerge"
plugin_info["pull_package"] = "PullPackage"
plugin_info["pull_framework"] = "PullFramework"


def show_help():
    print(f"Help: {os.path.basename(sys.argv[0])} [-h/--help]")
    print(f"Help plugin: {os.path.basename(sys.argv[0])} help plugin")
    print(f"Usage1: {os.path.basename(sys.argv[0])} plugin_name [plugin_args ...]")
    print(f"\tSupport input prefix. (eg. `apk_m` for `apk_merge`).")
    print(f"Usage2: {os.path.basename(sys.argv[0])} all [plugin_args ...]")
    print(f"Available plugins:\n\t{', '.join(plugin_info)}")
    exit(0)


def load_plugin(_plugin_name: str) -> Dp3Plugin:
    logging.debug("load plugin %s", _plugin_name)
    plugin_m = importlib.import_module(_plugin_name)
    return plugin_m.__getattribute__(plugin_info[_plugin_name])


def smart_choose(_guess: str) -> List[str]:
    return [x for x in plugin_info if _guess.lower() == 'all' or x.startswith(_guess)]


def choose_plugin(_plugin_name: str) -> str:
    guess_plugin = smart_choose(_plugin_name)
    if len(guess_plugin) == 0:
        print("cannot find plugin", _plugin_name)
        exit(0)
    elif len(guess_plugin) == 1:
        return guess_plugin[0]
    elif len(guess_plugin) > 1:
        print("which plugin do you want?")
        for idx, val in enumerate(guess_plugin):
            print(f"[{idx}]: {val}")
        return guess_plugin[int(input("input your choice "))]


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        show_help()

    if sys.argv[1] == 'help':
        if len(sys.argv) < 3:
            print("parameter plugin name is required")
        else:
            # fix argv[0], which make output more friendly
            plugin_name = choose_plugin(sys.argv[2])
            sys.argv[0] = sys.argv[0] + ' ' + plugin_name
            load_plugin(plugin_name).help()
        exit(0)
    plugin_name = choose_plugin(sys.argv[1])
    plugin_args = sys.argv[2:]
    load_plugin(plugin_name).plugin_entry(*plugin_args)
