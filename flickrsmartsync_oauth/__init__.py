# -*- coding: utf-8 -*-
import argparse
import os
import logging
from logging.handlers import SysLogHandler
from sync import Sync
from local import Local
from remote import Remote

# TODO: get version from setup.cfg
version = '0.1.0'

logging.basicConfig()
logger = logging.getLogger("flickrsmartsync_oauth")
hdlr = SysLogHandler()
formatter = logging.Formatter('flickrsmartsync_oauth %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

# flickrsmartsync_oauth.main()
def main():
    parser = argparse.ArgumentParser(description='Sync current folder to your flickr account.')

    parser.add_argument('--monitor',                action='store_true',            help='Start monitoring daemon.')
    parser.add_argument('--starts-with',                                type=str,   help='Only sync those paths that start with this text, e.g. "2015/06."')
    parser.add_argument('--download',                                   type=str,   help='Download photos from flickr. Specify a path or use "." for all.')
    parser.add_argument('--dry-run',                action='store_true',            help='Do not download or upload anything.')
    parser.add_argument('--ignore-videos',          action='store_true',            help='Ignore video files.')
    parser.add_argument('--ignore-images',          action='store_true',            help='Ignore image files.')
    parser.add_argument('--ignore-ext',                                 type=str,   help='Comma separated list of filename extensions to ignore, e.g. "jpg,png".')
    parser.add_argument('--fix-missing-description',action='store_true',            help='Replace missing set description with set title.')
    parser.add_argument('--version',                action='store_true',            help='Output current version: ' + version)
    parser.add_argument('--sync-path',                                  type=str,   default=os.getcwd(),  help='Specify sync path (default: current dir).')
    parser.add_argument('--sync-from',                                  type=str,   help='Only one supported value: "all". Upload anything not on flickr. Download anything not on the local filesystem.')
    parser.add_argument('--custom-set',                                 type=str,   help='Customize set name from path with regex, e.g. "(.*)/(.*)".')
    parser.add_argument('--custom-set-builder',                         type=str,   help='Build custom set title, e.g. "{0} {1}" joins first two groups (default behavior merges groups using a hyphen).')
    parser.add_argument('--update-custom-set',      action='store_true',            help='Updates set title from custom-set (and custom-set-builder, if given).')
    parser.add_argument('--custom-set-debug',       action='store_true',            help='When testing custom sets: ask for confirmation before creating an album.')
    parser.add_argument('--username',                                   type=str,   help='Token username argument for API.')
    parser.add_argument('--keyword',                action='append',    type=str,   help='Only upload files matching this keyword.')

    args = parser.parse_args()

    if args.version:
        logger.info(version)
        exit()

    # Windows OS
    args.is_windows = os.name == 'nt'
    args.sync_path = args.sync_path.rstrip(os.sep) + os.sep
    if not os.path.exists(args.sync_path):
        logger.error('Sync path does not exist.')
        exit(0)

    local = Local(args)
    remote = Remote(args)
    sync = Sync(args, local, remote)
    sync.start_sync()

