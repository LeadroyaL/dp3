#!/usr/bin/env python3

import glob
import subprocess
import os
import zipfile
from typing import Callable

from dp3_plugin import Dp3Plugin


def pull_dir(remote_path: str, force=False, _filter: Callable[[str], bool] = None):
    _proc = subprocess.Popen(['adb', 'shell', 'ls', remote_path, ], stdout=subprocess.PIPE)
    _proc.wait()
    for _line in _proc.stdout.readlines():
        _file = _line.decode().strip()
        if _filter and not _filter(_file):
            print("skip %s" % _file)
        else:
            if os.path.exists(_file) and not force:
                print("Exits %s" % _file)
            else:
                subprocess.Popen(['adb', 'pull', remote_path + '/' + _file]).wait()


def extract_one_vdex(vdex_path):
    print("extracting %s" % vdex_path)
    os.system("vdexExtractor --ignore-crc-error -i %s" % vdex_path)
    dex_name = vdex_path.replace(".vdex", "_classes.dex")
    cdex_name = vdex_path.replace(".vdex", "_classes.cdex")
    if os.path.exists(dex_name):
        print("got a dex")
    elif os.path.exists(cdex_name):
        print("got a cdex")
        os.system("cdexExtractor %s" % cdex_name)
        _cdex_suffix = 2
        while os.path.exists(cdex_name.replace(".cdex", "%d.cdex" % _cdex_suffix)):
            os.system("cdexExtractor %s" % cdex_name.replace(".cdex", "%d.cdex" % _cdex_suffix))
            _cdex_suffix += 1
    else:
        input("vdex FAIL, maybe no data in vdex. 任意键继续")


ANDROID_8 = 26
ANDROID_81 = 27
ANDROID_9 = 28
ANDROID_10 = 29
ANDROID_11 = 30


def check_zip_header(_full_path) -> bool:
    with open(_full_path, 'rb') as _fd:
        if _fd.read(4) == b'PK\x03\x04':
            return True
    return False


# ------------------------
# TODO:https://github.com/testwhat/SmaliEx
# meizu_mx3: 5 API[21] /system/framework/*.jar
# Honor7: 5 API[21] /system/framework/arm64/boot.oat /system/framework/arm64/*.odex
# MiNote: 6 API[23] /system/framework/oat/boot.oat /system/framework/oat/arm/*.odex
# ------------------------
# vivoU1:  8 API[27] /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex
# XiaoMi8: 9 API[28] /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex
# Redmi8A: 9 API[28] /system/framework/arm/*.vdex /system/framework/oat/arm/*.vdex
# SM-A6060:  10 API[29] /system/framework/*.jar /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex
# HW-P30:    10 API[29] /system/framework/*.jar /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex
# HW-Mate30: 10 API[29] /system/framework/*.jar /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex
# iqoo:      10 API[29] /system/framework/*.jar /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex
# oppo-reno3:10 API[29] /system/framework/*.jar /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex
# vivo-X27:  10 API[29] /system/framework/*.jar /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex
# pixel3:    11 API[30] /system/framework/*.jar /system/framework/arm64/*.vdex /system/framework/oat/arm64/*.vdex

def pull_framework():
    sdk_version = int(subprocess.Popen(['adb', 'shell', 'getprop', 'ro.build.version.sdk', ], stdout=subprocess.PIPE).stdout.read().strip())
    if ANDROID_10 <= sdk_version <= ANDROID_11:
        abilist = subprocess.Popen(['adb', 'shell', 'getprop', 'ro.product.cpu.abilist', ], stdout=subprocess.PIPE).stdout.read().strip().decode()
        if 'arm64' not in abilist:
            raise RuntimeError("SDK[%d] with arm32???" % sdk_version)
        pull_dir("/system/framework/oat/arm64", False, lambda remote_file: remote_file.endswith(".vdex"))
        pull_dir("/system/framework/arm64", False, lambda remote_file: remote_file.endswith(".vdex"))
        pull_dir("/system/framework", False, lambda remote_file: remote_file.endswith(".jar"))
    elif ANDROID_8 <= sdk_version <= ANDROID_9:
        abilist = subprocess.Popen(['adb', 'shell', 'getprop', 'ro.product.cpu.abilist', ], stdout=subprocess.PIPE).stdout.read().strip().decode()
        if 'arm64' in abilist:
            pull_dir("/system/framework/oat/arm64", False, lambda remote_file: remote_file.endswith(".vdex"))
            pull_dir("/system/framework/arm64", False, lambda remote_file: remote_file.endswith(".vdex"))
        else:
            pull_dir("/system/framework/oat/arm", False, lambda remote_file: remote_file.endswith(".vdex"))
            pull_dir("/system/framework/arm", False, lambda remote_file: remote_file.endswith(".vdex"))
    else:
        raise RuntimeError("Current version only test on 8.0<=Version<=11.0 ")

    for f in os.listdir('.'):
        if f.endswith('.vdex'):
            extract_one_vdex(f)
        elif f.endswith('.jar') and check_zip_header(f):
            z = zipfile.ZipFile(f)
            has_dex = "classes.dex" in z.namelist()
            z.close()
            if has_dex:
                os.rename(f, f.replace('.jar', '.apk'))
            else:
                os.unlink(f)
    [os.unlink(x) for x in glob.glob("*.cdex")]
    [os.unlink(x) for x in glob.glob("*.vdex")]
    [os.rename(x, x.replace('.cdex.new', '.dex')) for x in glob.glob("*.cdex.new")]


if __name__ == '__main__':
    pull_framework()


class PullFramework(Dp3Plugin):
    @staticmethod
    def plugin_entry(*_argv: str):
        pull_framework()
