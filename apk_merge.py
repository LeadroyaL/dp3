#!/usr/bin/env python3

import datetime
import argparse
import glob
import logging
import os
import shutil
import sys
from fnmatch import fnmatch
from itertools import chain
from typing import List
from zipfile import ZipFile

from dp3_plugin import Dp3Plugin

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-5.5s] %(module)s %(message)s")

DEFAULT_MERGED_FILE = 'merged_TIME.apk'


def parse_arg(*_argv: str) -> (argparse.Namespace, list):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--output', dest='merged_file', metavar="output", action='store', help='output file', default=DEFAULT_MERGED_FILE)
    parser.add_argument('-f', dest='force', action='store_true', help='force overwrite file')
    parser.add_argument('files', nargs='+', help='apk/dex/jar files or directory to be merged')
    return parser.parse_known_args(_argv)


class ApkFile:
    def __init__(self, filepath: str, mode: str = 'r'):
        self.filepath: str = filepath
        self.mode: str = mode
        self.z: ZipFile = ZipFile(self.filepath, self.mode)
        self.maxIdx: int = len(self.list_dex())

    def __enter__(self) -> 'ApkFile':
        logging.debug("enter %s", self.filepath)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug("exit %s", self.filepath)
        self.z.close()

    def has_dex(self) -> bool:
        return self.z.NameToInfo.get('classes.dex') is not None

    def list_dex(self) -> List[str]:
        return [fn for fn in self.z.namelist() if fnmatch(fn, "classes*.dex")]

    def merge_dex(self, other_dex: str):
        logging.info("merge(%s, %s)", self, other_dex)
        self.z.write(other_dex, self.__next_classes_name())

    def merge_apk(self, other_apk: 'ApkFile'):
        logging.info("merge(%s, %s)", self, other_apk)
        for other_dex in other_apk.list_dex():
            self.z.writestr(self.__next_classes_name(), other_apk.z.read(other_dex))

    def __next_classes_name(self):
        self.maxIdx += 1
        if self.maxIdx == 1:
            return "classes.dex"
        else:
            return "classes%d.dex" % self.maxIdx

    def __repr__(self):
        return "<ApkFile %s>" % self.filepath


def main(*_argv: str):
    args, _ = parse_arg(*_argv)

    if len(args.files) < 2 and not os.path.isdir(args.files[0]):
        raise RuntimeError("You need at least one directory or two apk files")
    merged_file: str = args.merged_file

    if merged_file == DEFAULT_MERGED_FILE:
        merged_file = 'merged_%s.apk' % datetime.datetime.now().strftime("%H%M%S")

    if os.path.exists(merged_file) and not args.force:
        raise RuntimeError("%s file exits, please use -f overwrite it." % merged_file)

    logging.info("touch file")
    with open(merged_file, 'wb'):
        pass

    if os.path.isfile(args.files[0]) and args.files[0].endswith('.apk'):
        with ApkFile(args.files[0]) as _main_apk:
            if _main_apk.has_dex():
                logging.debug("copy file")
                # Maybe resources file is useful, we keep the whole file of main apk.
                shutil.copy(_main_apk.filepath, merged_file)
                args.files.pop(0)

    with ApkFile(merged_file, 'a') as main_apk:
        for todo in args.files:
            if os.path.isdir(todo):
                for dex in glob.iglob(todo + "/**/*.dex", recursive=True):
                    main_apk.merge_dex(dex)
                for apk in chain(glob.iglob(todo + "/**/*.zip", recursive=True),
                                 glob.iglob(todo + "/**/*.apk", recursive=True)):
                    with ApkFile(apk) as _other_apk:
                        main_apk.merge_apk(_other_apk)
            elif todo.endswith('.dex'):
                main_apk.merge_dex(todo)
            else:
                with ApkFile(todo) as _other_apk:
                    main_apk.merge_apk(_other_apk)
        logging.info("Finished! Total dex %d", main_apk.maxIdx)


if __name__ == '__main__':
    main(*sys.argv[1:])


class ApkMerge(Dp3Plugin):
    @staticmethod
    def plugin_entry(*_argv: str):
        main(*_argv)

    @staticmethod
    def help():
        main("--help")
