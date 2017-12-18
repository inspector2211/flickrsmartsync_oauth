import logging
import os

from iptcinfo import IPTCInfo

logger = logging.getLogger(__name__) # create logger

class Local(object):
    def __init__(self, parser_args):
        self.parser_args = parser_args

    def build_local_photo_sets(self, path, valid_extensions): # build local photo sets
        local_photo_sets = {}
        keywords = set(self.parser_args.keywords) if self.parser_args.keywords else ()

        for root_dir, dirs, files in os.walk(path, followlinks=True):

            if self.parser_args.starts_with and not root_dir.startswith('{}{}'.format(self.parser_args.sync_path, self.parser_args.starts_with)):
                logger.debug('skipping local directory "%s" (--starts-with="%s" not satisfied)', root_dir, self.parser_args.starts_with)
                continue

            files = [f for f in files if not f.startswith('.')]

            for file in files:
                file_path = os.path.join(root_dir, file)
                file_stat = os.stat(file_path)

                file_extension = file.lower().split('.').pop()

                if file_extension not in valid_extensions:
                    #logger.debug('skipping local file "%s" (unrecognized filename extension; valid extensions are: %s)', file_path, list(valid_extensions)) #TODO too many files
                    continue

                if root_dir == self.parser_args.sync_path:
                    logger.info('skipping local file "%s" (files in --sync-path root are not synced to avoid disorganized flickr sets)', file_path)
                    continue

                if keywords:
                    file_info = IPTCInfo(file_path, force=True) # use "force=True" if file may not have IPTC metadata

                    if not keywords.intersection(file_info.keywords):
                        logger.debug('skipping local file "%s" (--keywords=%s not satisfied)', file_path, list(keywords))
                        continue

                local_photo_sets.setdefault(root_dir, [])
                local_photo_sets[root_dir].append((file, file_stat))
        return local_photo_sets
