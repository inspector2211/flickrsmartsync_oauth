import HTMLParser
import flickrapi
import json
import logging
import os
import re
import urllib

"""
    1. To use this script, you must apply for your own private Flickr API keys
    2. Visit URL
       https://www.flickr.com/services/api/misc.api_keys.html
    3. Apply for your key online
    4. Apply for a non-commercial key
    5. Store your API keys in a file named config.py with the following format
       api_key = 'key'
       api_secret = 'secret'
    6. Import keys below
"""
import config # API keys

num_retries = 3 # number of retries for uploads

logger = logging.getLogger(__name__) # create logger

class Remote(object):
    def __init__(self, parser_args):
        self.parser_args = parser_args
        self.args = {'format': 'json', 'nojsoncallback': 1}

        self.auth_api()
        self.build_remote_photo_sets()

    def auth_api(self):
        self.api = flickrapi.FlickrAPI(config.api_key, config.api_secret)

        if not self.api.token_valid(perms=u'delete'):
            logger.info('authentication token invalid or not present: attempting to reauthenticate (--nobrowser supports manual authentication when no web browser is available)')
            try:
                if self.parser_args.nobrowser:
                    self.api.get_request_token(oauth_callback='oob')
                    auth_url = self.api.auth_url(perms=u'delete')
                    logger.info('authentication URL: %s', auth_url)
                    auth_code = str(raw_input('enter code from authentication URL: '))
                    self.api.get_access_token(unicode(auth_code))
                else:
                    self.api.authenticate_via_browser(perms=u'delete')
            except:
                logger.error('authentication failed')
                exit(0)

    def custom_set_title(self, path):
        if self.parser_args.custom_set: # customize set title from full path using standard regex, e.g. "(.*)/(.*)"
            m = re.match(self.parser_args.custom_set, path)
            if m:
                if not self.parser_args.custom_set_builder: # default behavior merges matched groups using a hyphen
                    title = '-'.join(m.groups())
                elif m.groupdict(): # else build custom set title using dictionary indexing
                    title = self.parser_args.custom_set_builder.format(**m.groupdict())
                else: # else build custom set title using matched groups, e.g. "{0}{1}" joins first two "(.*)/(.*)"
                    title = self.parser_args.custom_set_builder.format(*m.groups())
        else: # else use directory name
            title = path.split('/').pop()
        return title

    def build_remote_photo_sets(self): # build remote photo sets
        self.remote_photo_sets = {}
        remote_photo_sets_args = self.args.copy()

        html_parser = HTMLParser.HTMLParser()

        page = 0

        while True:
            page += 1
            remote_photo_sets_args.update({
                'page'    : page,
                'per_page': 500
            })

            logger.debug('getting remote photosets, page %2s' % page)
            sets = json.loads(self.api.photosets_getList(**remote_photo_sets_args))

            if not sets['photosets']['photoset']: break

            for current_set in sets['photosets']['photoset']:
                photo_set = html_parser.unescape(current_set['description']['_content']) # each photo set is indexed using description
                photo_set = photo_set.encode('utf-8') if isinstance(photo_set, unicode) else photo_set

                if not photo_set and self.parser_args.fix_missing_description: # if no description
                    title = html_parser.unescape(current_set['title']['_content'])
                    title = title.encode('utf-8') if isinstance(title, unicode) else title

                    fix_missing_description_args = self.args.copy()
                    fix_missing_description_args.update({
                        'photoset_id': current_set['id'],
                        'title'      : title,
                        'description': title # replace missing description with title
                    })

                    if self.parser_args.dry_run:
                        logger.info('(--dry-run) --fix-missing-description for "%s"' % title)
                    else:
                        logger.debug('--fix-missing-description for "%s"' % title)
                        json.loads(self.api.photosets_editMeta(**fix_missing_description_args))

                    photo_set = title # update description with title

                if photo_set: # if description
                    title = self.custom_set_title(self.parser_args.sync_path + photo_set)

                    if title != current_set['title']['_content']: # update title if necessary
                        custom_set_args = self.args.copy()
                        custom_set_args.update({
                            'photoset_id': current_set['id'],
                            'title'      : title,
                            'description': photo_set
                        })

                        if self.parser_args.dry_run:
                            logger.info('(--dry-run) --custom-set title "%s"' % title)
                        else:
                            logger.debug('--custom-set title "%s"' % title)
                            json.loads(self.api.photosets_editMeta(**custom_set_args))

                    self.remote_photo_sets[photo_set] = current_set['id'] # add current photo set to dictionary of remote photo sets

    def get_photo_sets(self):
        return self.remote_photo_sets

    def add_photo_to_set(self, photo_id, photo_set):
        if self.parser_args.windows: # always upload UNIX style
            photo_set = photo_set.replace(os.sep, '/')

        if photo_set not in self.remote_photo_sets: # create photo set if not found in remote map
            title = self.custom_set_title(self.parser_args.sync_path + photo_set)

            remote_photo_sets_args = self.args.copy()
            remote_photo_sets_args.update({'primary_photo_id': photo_id, # index photo
                                           'title'           : title,
                                           'description'     : photo_set
            })

            if self.parser_args.dry_run:
                logger.info('(--dry-run) created set "%s"' % photo_set)
                logger.info('(--dry-run) added photo to set "%s"' % photo_set)
            else:
                logger.debug('created set "%s"' % photo_set)
                logger.debug('added photo to set "%s"' % photo_set)

                new_photo_set = json.loads(self.api.photosets_create(**remote_photo_sets_args))
                self.remote_photo_sets[photo_set] = new_photo_set['photoset']['id']

        else: # else add photo to existing set
            remote_photo_sets_args = self.args.copy()
            remote_photo_sets_args.update({'photoset_id': self.remote_photo_sets.get(photo_set),
                                           'photo_id'   : photo_id
            })

            if self.parser_args.dry_run:
                logger.info('(--dry-run) added photo to set "%s"' % photo_set)
            else:
                result = json.loads(self.api.photosets_addPhoto(**remote_photo_sets_args))
                if result.get('stat') == 'ok':
                    logger.debug('added photo to set "%s"' % photo_set)
                else:
                    logger.info('failed to add photo to set "%s"' % photo_set)
                    logger.error(result)

    def upload(self, path, photo, photo_set):
        upload_args = {
            'title'       : photo,     # (optional) title
            'description' : photo_set, # (optional) description
            'is_public'   : 0,         # (optional) visible to everyone (0: no, 1: yes)
            'is_friend'   : 0,         # (optional) visible to friends  (0: no, 1: yes)
            'is_family'   : 0,         # (optional) visible to family   (0: no, 1: yes)
            'safety_level': 1,         # (optional) safety level (1: safe, 2: moderate, 3: restricted)
            'content_type': 1,         # (optional) content type (1: photo, 2: screenshot, 3: other)
            'hidden'      : 2          # (optional) search (1: appears in global search results, 2: hidden from public searches)
        }

        for i in range(num_retries):
            try:
                upload = self.api.upload(path, None, **upload_args)

                photo_id = upload.find('photoid').text
                self.add_photo_to_set(photo_id, photo_set)
                return photo_id
            except Exception as e:
                logger.warning('caught exception during upload (%s)' % e)

        logger.error('failed to upload "%s/%s" after %d attempts' % (photo_set, photo, num_retries))

    def download(self, url, path):
        folder = os.path.dirname(path)
        if not os.path.isdir(folder): os.makedirs(folder)   

        for i in range(num_retries):
            try:
                return urllib.urlretrieve(url, path)
            except Exception as e:
                logger.warning('caught exception during download (%s)' % e)

        logger.error('failed to download "%s" after %d attempts' % (path, num_retries))

    def get_photos_in_set(self, photo_set, get_url=False):
        photos = {}
        photo_set = photo_set.encode('utf-8') if isinstance(photo_set, unicode) else photo_set

        if self.parser_args.windows: # always upload UNIX style
            photo_set = photo_set.replace(os.sep, '/')

        if photo_set in self.remote_photo_sets:
            page = 0
            photoset_args = self.args.copy()

            while True:
                page += 1
                photoset_args.update({'photoset_id': self.remote_photo_sets[photo_set],
                                      'page'       : page
                })
                if get_url: photoset_args['extras'] = 'url_o,media'

                photos_in_set = json.loads(self.api.photosets_getPhotos(**photoset_args))
                if photos_in_set['stat'] != 'ok':
                    #logger.info('failed to get photos in set "%s"' % photo_set) #TODO set name will incorrectly log error
                    #logger.error(photos_in_set['stat'])
                    break

                for photo in photos_in_set['photoset']['photo']:
                    title = photo['title'].encode('utf-8')
                    split = title.split(".") # add missing file extension if not present

                    if len(split) < 2 or len(split[-1]) > 4: # assume valid file extension is <= 4 chars
                        if photo.get('media') == 'video': #TODO take a guess as API original_format argument not working
                            title += ".mp4"
                        else:
                            title += ".jpg"

                    if get_url:
                        media = photo.get('media')

                        if media == 'video':
                            photo_args = self.args.copy()
                            photo_args['photo_id'] = photo['id']

                            sizes = json.loads(self.api.photos_getSizes(**photo_args)) # return available sizes for video media
                            if sizes['stat'] != 'ok':
                                logger.info('failed to get sizes for %s "%s" in set "%s"' % (media, title, photo_set))
                                logger.error(sizes['stat'])
                                continue

                            original_size = filter(lambda s: s['label'].startswith('Video Original') and s['media'] == 'video', sizes['sizes']['size'])
                            if original_size:
                                photos[title] = original_size.pop()['source']
                        else:
                            photos[title] = photo['url_o']
                    else:
                        photos[title] = photo['id']
        return photos
