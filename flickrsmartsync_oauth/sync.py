import logging
import os

EXT_IMAGE = (
             'jpg',
             'jpeg',
             'png',
             'gif',
             'tif',
             'tiff',
             'bmp'
            )
EXT_VIDEO = (
             'm4v',
             'mp4',
             'avi',
             'wmv',
             'mov',
             'mpg',
             'mpeg',
             '3gp',
             'mts',
             'm2ts',
             'ogg',
             'ogv')

IMAGE_MAX_SIZE =      200 * 1024 * 1024 # 200MB
VIDEO_MAX_SIZE = 1 * 1024 * 1024 * 1024 # 1GB

logger = logging.getLogger(__name__) # create logger

class Sync(object):
    def __init__(self, parser_args, local, remote):
        global EXT_IMAGE, EXT_VIDEO, IMAGE_MAX_SIZE, VIDEO_MAX_SIZE
        global valid_extensions

        self.parser_args = parser_args

        if self.parser_args.ignore_extensions: # comma separated list of filename extensions to ignore
            ignore_extensions = self.parser_args.ignore_extensions.split(',')
            EXT_IMAGE = filter(lambda e: e not in ignore_extensions, EXT_IMAGE)
            EXT_VIDEO = filter(lambda e: e not in ignore_extensions, EXT_VIDEO)
        valid_extensions = EXT_IMAGE + EXT_VIDEO

        self.local = local
        self.remote = remote

    def start_sync(self):
        if self.parser_args.sync:
                logger.debug('syncing...')
                self.sync()
        elif self.parser_args.download: # download photos; specify a path or use "." for all
                logger.debug('downloading...')
                self.download()
        else:
                logger.debug('uploading...')
                self.upload()

    def sync(self):
        local_photo_sets = self.local.build_local_photo_sets(self.parser_args.sync_path, valid_extensions)
        remote_photo_sets = self.remote.get_photo_sets()

        for remote_photo_set in remote_photo_sets: # for remote sets
            local_photo_set = os.path.join(self.parser_args.sync_path, remote_photo_set).replace("/", os.sep)

            if local_photo_set not in local_photo_sets: # download remote set if local set not present
                if self.parser_args.dry_run:
                    logger.info('(--dry-run) downloading photo set "%s"' % remote_photo_set)
                else:
                    logger.debug('downloading photo set "%s"' % remote_photo_set)
                    self.parser_args.download = local_photo_set
                    self.download()

        for local_photo_set in sorted(local_photo_sets): # for local sets
            remote_photo_set = local_photo_set.replace(self.parser_args.sync_path, '').replace(os.sep, "/") # remote sets always use UNIX style

            if remote_photo_set not in remote_photo_sets: remote_photos = {} # upload local set if remote set not present
            else: remote_photos = self.remote.get_photos_in_set(remote_photo_set, get_url=True)

            local_photos = [photo for photo, file_stat in sorted(local_photo_sets[local_photo_set])]

            for photo in [photo for photo in remote_photos if photo not in local_photos]: # download remote photo if local not present
                path = os.path.join(local_photo_set, photo)

                if self.parser_args.dry_run:
                    logger.info('(--dry-run) downloading "%s"' % path)
                else:
                    logger.info('downloading "%s"' % path)
                    self.remote.download(remote_photos[photo], path)

            for photo in [photo for photo in local_photos if photo not in remote_photos]: # upload local photo if remote not present
                file_path = os.path.join(local_photo_set, photo)
                file_stat = os.stat(file_path)

                if self.parser_args.ignore_images and photo.split('.').pop().lower() in EXT_IMAGE:
                    logger.debug('skipping photo "%s" (--ignore-images)' % photo)
                    continue
                elif self.parser_args.ignore_videos and photo.split('.').pop().lower() in EXT_VIDEO:
                    logger.debug('skipping video "%s" (--ignore-videos)' % photo)
                    continue

                if file_stat.st_size >= IMAGE_MAX_SIZE and photo.split('.').pop().lower() in EXT_IMAGE:
                    logger.info('skipping photo "%s" (exceeds IMAGE_MAX_SIZE)' % photo)
                    continue
                if file_stat.st_size >= VIDEO_MAX_SIZE and photo.split('.').pop().lower() in EXT_VIDEO:
                    logger.info('skipping video "%s" (exceeds VIDEO_MAX_SIZE)' % photo)
                    continue

                if self.parser_args.dry_run:
                    logger.info('(--dry-run) uploading "%s" to set "%s"' % (photo, remote_photo_set))
                else:
                    logger.debug('uploading "%s" to set "%s"' % (photo, remote_photo_set))
                    self.remote.upload(file_path, photo, remote_photo_set)

    def download(self):
        for photo_set in self.remote.get_photo_sets():
            if photo_set and (self.parser_args.download == '.' or photo_set.startswith(self.parser_args.download)):
                folder = os.path.join(self.parser_args.sync_path, photo_set)

                if self.parser_args.windows: # always upload UNIX style
                    folder = folder.replace('/', os.sep)

                remote_photos = self.remote.get_photos_in_set(photo_set, get_url=True)

                for photo in remote_photos:
                    path = os.path.join(folder, photo)

                    if self.parser_args.ignore_images and photo.split('.').pop().lower() in EXT_IMAGE:
                        logger.debug('skipping photo "%s" (--ignore-images)' % photo)
                        continue
                    elif self.parser_args.ignore_videos and photo.split('.').pop().lower() in EXT_VIDEO:
                        logger.debug('skipping video "%s" (--ignore-videos)' % photo)
                        continue

                    if os.path.exists(path):
                        #logger.debug('skipping "%s" (already exists)' % path) #TODO too many files
                        pass
                    elif self.parser_args.dry_run:
                        logger.info('(--dry-run) downloading "%s"' % path)
                    else:
                        logger.info('downloading "%s"' % path)
                        self.remote.download(remote_photos[photo], path)

    def upload(self):
        local_photo_sets = self.local.build_local_photo_sets(self.parser_args.sync_path, valid_extensions)

        for photo_set in sorted(local_photo_sets):
            title = self.remote.custom_set_title(photo_set)

            folder = photo_set.replace(self.parser_args.sync_path, '')

            remote_photos = self.remote.get_photos_in_set(folder)

            for photo, file_stat in sorted(local_photo_sets[photo_set]):
                file_path = os.path.join(photo_set, photo)                        

                if self.parser_args.ignore_images and photo.split('.').pop().lower() in EXT_IMAGE:
                    logger.debug('skipping photo "%s" (--ignore-images)' % photo)
                    continue
                elif self.parser_args.ignore_videos and photo.split('.').pop().lower() in EXT_VIDEO:
                    logger.debug('skipping video "%s" (--ignore-videos)' % photo)
                    continue

                if photo in remote_photos or (self.parser_args.windows and photo.replace(os.sep, '/')) in remote_photos:
                    #logger.debug('skipping "%s" in "%s" (already exists)' % (photo, title)) #TODO too many files
                    pass
                else:
                    if file_stat.st_size >= IMAGE_MAX_SIZE and photo.split('.').pop().lower() in EXT_IMAGE:
                        logger.info('skipping photo "%s" (exceeds IMAGE_MAX_SIZE)' % photo)
                        continue
                    if file_stat.st_size >= VIDEO_MAX_SIZE and photo.split('.').pop().lower() in EXT_VIDEO:
                        logger.info('skipping video "%s" (exceeds VIDEO_MAX_SIZE)' % photo)
                        continue

                    if self.parser_args.dry_run:
                        logger.info('(--dry-run) uploading "%s" to "%s"' % (photo, title))
                    else:
                        logger.debug('uploading "%s" to "%s"' % (photo, title))
                        photo_id = self.remote.upload(file_path, photo, folder)
                        if photo_id:
                            remote_photos[photo] = photo_id
