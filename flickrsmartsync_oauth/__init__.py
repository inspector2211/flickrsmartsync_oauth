import argparse
import logging
import os

from local import Local
from remote import Remote
from sync import Sync

logger = logging.getLogger(__name__) # create logger
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler() # send INFO to console
ch.setLevel(logging.INFO)

fh = logging.FileHandler('flickrsmartsync_oauth.log', mode='w') # send DEBUG to log file
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(levelname)7s, %(name)-28s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S') # create formatter

ch.setFormatter(formatter) # add formatter to handlers
fh.setFormatter(formatter)

logger.addHandler(ch) # add handlers to logger
logger.addHandler(fh)

version = '1.0.0'

def main():
    parser = argparse.ArgumentParser(description='Upload, download or sync photos and videos to Flickr.')
    parser.add_argument('--custom-set',                                   type=str,                         help='customize set title from path using standard regex, e.g. "(.*)/(.*)"')
    parser.add_argument('--custom-set-builder',                           type=str,                         help='build a custom set title using matched groups, e.g. "{0}{1}" joins first two "(.*)/(.*)"')
    parser.add_argument('--download',                                     type=str,                         help='download photos; specify a path or use "." for all')
    parser.add_argument('--dry-run',                 action='store_true',                                   help='report actions but do not change local/remote sets')
    parser.add_argument('--fix-missing-description', action='store_true',                                   help='replace missing set description with set title')
    parser.add_argument('--ignore-extensions',                            type=str,                         help='comma separated list of filename extensions to ignore')
    parser.add_argument('--ignore-images',           action='store_true',                                   help='ignore image files: jpg, jpeg, png, gif, tif, tiff, bmp')
    parser.add_argument('--ignore-videos',           action='store_true',                                   help='ignore video files: m4v, mp4, avi, wmv, mov, mpg, mpeg, 3gp, mts, m2ts, ogg, ogv')
    parser.add_argument('--keywords',                action='append',     type=str,                         help='only upload files with IPTC metadata matching these keywords')
    parser.add_argument('--nobrowser',               action='store_true',                                   help='support manual authentication when no web browser is available')
    parser.add_argument('--starts-with',                                  type=str,                         help='only upload paths starting with this text')
    parser.add_argument('--sync',                    action='store_true',                                   help='upload anything not on Flickr; download anything not on local filesystem')
    parser.add_argument('--sync-path',                                    type=str,   default=os.getcwd(),  help='sync path (default: current dir); individual files in --sync-path root are not synced to avoid disorganized Flickr sets')
    parser.add_argument('--version',                 action='store_true',                                   help='print current version: ' + version)

    args = parser.parse_args()

    args.windows = os.name == "nt"

    if args.version:
        logger.info('--version %s', version)
        exit(0)
    else:
        logger.debug('--version %s', version)

    args.sync_path = args.sync_path.rstrip(os.sep) + os.sep # ensure sync path ends with "/"
    if not os.path.exists(args.sync_path):
        logger.error('--sync-path "%s" does not exist', args.sync_path)
        exit(0)

    local = Local(args)
    remote = Remote(args)
    sync = Sync(args, local, remote)
    sync.start_sync()
