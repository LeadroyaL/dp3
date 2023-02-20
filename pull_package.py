#!/usr/bin/env python3
import argparse
import subprocess
import zipfile
import os
import glob
import sys
from typing import *

from dp3_plugin import Dp3Plugin


def insert_vdex_to_apk(vdex_name: str, apk_path: str):
    os.system("vdexExtractor -i %s" % vdex_name)
    z = zipfile.ZipFile(apk_path, 'a')
    dex_name = vdex_name.replace(".vdex", "_classes.dex")
    cdex_name = vdex_name.replace(".vdex", "_classes.cdex")
    if os.path.exists(dex_name):
        print("got a dex")
        z.write(dex_name, "classes.dex")
        _ = 2
        while os.path.exists(dex_name.replace(".dex", "%d.dex" % _)):
            z.write(dex_name.replace(".dex", "%d.dex" % _), "classes%d.dex" % _)
            _ += 1
    elif os.path.exists(cdex_name):
        print("got a cdex")
        os.system("cdexExtractor %s" % cdex_name)
        z.write(cdex_name + ".new", "classes.dex")
        _ = 2
        while os.path.exists(cdex_name.replace(".cdex", "%d.cdex" % _)):
            os.system("cdexExtractor %s" % cdex_name.replace(".cdex", "%d.cdex" % _))
            z.write(cdex_name.replace(".cdex", "%d.cdex" % _) + '.new', "classes%d.dex" % _)
            _ += 1
    else:
        raise Exception("TODO: vdex FAIL")


def pull_one_pkg(pkg: str, remote_path: str, force=False, _filter: Callable[[str], bool] = None):
    remote_parent, remote_filename = os.path.split(remote_path)
    if _filter and not _filter(remote_path):
        print("skip %s" % remote_path)
        return
    if remote_path.endswith('/base.apk'):
        local_path = pkg + '.apk'
    else:
        local_path = remote_filename
    if os.path.exists(local_path) and not force:
        print("Exits %s" % local_path)
    else:
        subprocess.Popen(['adb', 'pull', remote_path, local_path]).wait()
    if not os.path.exists(local_path):
        return
    if remote_path.startswith("/data/"):
        print("Normal dex %s" % local_path)
        return
    z = zipfile.ZipFile(local_path)
    has_dex = "classes.dex" in z.namelist()
    z.close()
    if has_dex:
        print("Normal dex %s" % local_path)
    else:
        vdex_name = remote_filename.replace('.apk', '.vdex')
        if not os.path.exists(vdex_name) or force:
            if subprocess.Popen(['adb', 'pull', '%s/oat/arm/%s' % (remote_parent, vdex_name)], stdout=subprocess.DEVNULL).wait() == 0 or \
                    subprocess.Popen(['adb', 'pull', '%s/oat/arm64/%s' % (remote_parent, vdex_name)], stdout=subprocess.DEVNULL).wait() == 0:
                print("pull vdex success")
            else:
                print("Cannot find vdex for %s" % remote_path)
                return
        else:
            print("Exits %s" % vdex_name)
        if os.path.exists(vdex_name):
            insert_vdex_to_apk(vdex_name, local_path)


def get_pkgs(_cfg: argparse.Namespace = None) -> Dict[str, str]:
    _ret = dict()
    _cmd = ['adb', 'shell', 'pm', 'list', 'package', '-f']
    if _cfg:
        if _cfg.is3rd:
            _cmd.append('-3')
        if _cfg.isSystem:
            _cmd.append('-s')
    _proc = subprocess.Popen(_cmd, stdout=subprocess.PIPE)
    for _line in _proc.stdout.readlines():
        _line = _line.decode().replace('package:', '').strip()
        _full_path, _pkg_name = _line.rsplit('=', 1)
        _ret[_pkg_name] = _full_path
    return _ret


def pull_package(_keywords: Set[str], _cfg: argparse.Namespace = None) -> None:
    for pkg, full_path in get_pkgs(_cfg).items():
        if len(_keywords) == 0 or any(_keyword in pkg for _keyword in _keywords):
        # if len(_keywords) == 0 or any(_keyword == pkg for _keyword in _keywords):
            pull_one_pkg(pkg, full_path)
            # pull_one_pkg(pkg, full_path, False, lambda remote_path: remote_path.startswith("/data"))
    [os.unlink(x) for x in glob.glob("*.dex")]
    [os.unlink(x) for x in glob.glob("*.cdex")]
    [os.unlink(x) for x in glob.glob("*.vdex")]
    [os.unlink(x) for x in glob.glob("*.cdex.new")]


def parse_arg(*_argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-3', dest="is3rd", action='store_true', help='pm list pacakge -3: filter to only show third party packages', default=False)
    parser.add_argument('-s', dest="isSystem", action='store_true', help='pm list pacakge -s: filter to only show system packages', default=False)
    return parser.parse_known_args(_argv)


def main(*_argv):
    cfg, keywords = parse_arg(*_argv)
    pull_package(set(keywords), cfg)


if __name__ == '__main__':
    main(*sys.argv[1:])


class PullPackage(Dp3Plugin):
    @staticmethod
    def plugin_entry(*_argv: str):
        main(*_argv)

    @staticmethod
    def help():
        main("--help")
