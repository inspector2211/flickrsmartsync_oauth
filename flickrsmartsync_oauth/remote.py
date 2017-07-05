import HTMLParser
import json
import os
import re
import urllib
import flickrapi
import webbrowser
import logging
import config

logger = logging.getLogger("flickrsmartsync_oauth")

# number of retries for downloads
RETRIES = 10

class Remote(object):

    def __init__(self, cmd_args):
        # Command line arguments
        self.cmd_args = cmd_args
        self.auth_api() # removed return token

        # Common arguments
        self.args = {'format': 'json', 'nojsoncallback': 1} # removed auth_token

        # photo_sets_map[folder] = id
        self.update_photo_sets_map()

    def auth_api(self):
	# Store your flickr API key and secret in config.py:
	#
	# api_key = u'<API_KEY>'
	# api_secret = u'<API_SECRET>'
	#
        self.api = flickrapi.FlickrAPI(config.api_key, config.api_secret)

        # Authentication
        if not self.api.token_valid(perms=u'delete'):
            print('Authenticating...')
        try:
            self.api.authenticate_via_browser(perms=u'delete')
            """
            # Get a request token
            # self.api.get_request_token(oauth_callback='oob')
            self.api.get_request_token()

            # Open a browser at the authentication URL.
            authorize_url = self.api.auth_url(perms=u'delete')
            webbrowser.open_new_tab(authorize_url)

            # Get the verifier code from the user.
            verifier = str(input('Please enter verfication code: '))

            # Trade the request token for an access token
            # added unicode()
            self.api.get_access_token(unicode(verifier))
            """
        except:
            logger.error('Authentication is required.')
            exit(0)

    # Custom set builder
    def get_custom_set_title(self, path):
        title = path.split('/').pop()

        if self.cmd_args.custom_set:
            m = re.match(self.cmd_args.custom_set, path)
            if m:
                if not self.cmd_args.custom_set_builder:
                    # Default behavior merges groups using a hyphen
                    title = '-'.join(m.groups())
                elif m.groupdict():
                    title = self.cmd_args.custom_set_builder.format(**m.groupdict())
                else:
                    title = self.cmd_args.custom_set_builder.format(*m.groups())
        return title

    # Add photos to a set
    def add_to_photo_set(self, photo_id, folder):
        # Always upload UNIX style
        if self.cmd_args.is_windows:
            folder = folder.replace(os.sep, '/')

        # Create photo set if not found in remote map, else add photo to existing set
        if folder not in self.photo_sets_map:
            photosets_args = self.args.copy()
            custom_title = self.get_custom_set_title(self.cmd_args.sync_path + folder)
            photosets_args.update({'primary_photo_id': photo_id,
                                   'title': custom_title,
                                   'description': folder})
            photo_set = json.loads(self.api.photosets_create(**photosets_args))
            self.photo_sets_map[folder] = photo_set['photoset']['id']
            logger.info('Created set [%s] and added photo.' % custom_title)
        else:
            photosets_args = self.args.copy()
            photosets_args.update({'photoset_id': self.photo_sets_map.get(folder), 'photo_id': photo_id})
            result = json.loads(self.api.photosets_addPhoto(**photosets_args))
            if result.get('stat') == 'ok':
                logger.info('Added photo to set [%s].' % folder)
            else:
                logger.error(result)

    # Get photos in a set
    def get_photos_in_set(self, folder, get_url=False):
        # Bug on non utf8 machines dups
        folder = folder.encode('utf-8') if isinstance(folder, unicode) else folder

        photos = {}
        # Always upload UNIX style
        if self.cmd_args.is_windows:
            folder = folder.replace(os.sep, '/')

        if folder in self.photo_sets_map:
            photoset_args = self.args.copy()
            page = 1
            while True:
                photoset_args.update({'photoset_id': self.photo_sets_map[folder], 'page': page})
                if get_url:
                    photoset_args['extras'] = 'url_o,media'
                page += 1
                photos_in_set = json.loads(self.api.photosets_getPhotos(**photoset_args))
                if photos_in_set['stat'] != 'ok':
                    break

                for photo in photos_in_set['photoset']['photo']:
                    title = photo['title'].encode('utf-8')
                    # Add missing extension if not present (take a guess as API original_format argument not working)
                    split = title.split(".")
                    # Assume valid file extension is less than or equal to 5 characters and not all digits
                    if len(split) < 2 or len(split[-1]) > 5 or split[-1].isdigit():
                        if photo.get('media') == 'video':
                            title += ".mp4"
                        else:
                            title += ".jpg"
                    if get_url and photo.get('media') == 'video':
                        photo_args = self.args.copy()
                        photo_args['photo_id'] = photo['id']
                        sizes = json.loads(self.api.photos_getSizes(**photo_args))
                        if sizes['stat'] != 'ok':
                            continue

                        original = filter(lambda s: s['label'].startswith('Video Original') and s['media'] == 'video', sizes['sizes']['size'])
                        if original:
                            photos[title] = original.pop()['source']

                    else:
                        photos[title] = photo['url_o'] if get_url else photo['id']

        return photos

    def get_photo_sets(self):
        return self.photo_sets_map

    def update_photo_sets_map(self):
        # Get remote photo set map and compare to local map
        html_parser = HTMLParser.HTMLParser()
        photosets_args = self.args.copy()
        page = 1
        self.photo_sets_map = {}

        while True:
            logger.debug('Getting photosets page %s.' % page)
            photosets_args.update({'page': page, 'per_page': 500})
            sets = json.loads(self.api.photosets_getList(**photosets_args))
            page += 1
            if not sets['photosets']['photoset']:
                break

            for current_set in sets['photosets']['photoset']:
                # Make sure it's the one from backup format
                desc = html_parser.unescape(current_set['description']['_content'])
                desc = desc.encode('utf-8') if isinstance(desc, unicode) else desc

                if self.cmd_args.fix_missing_description and not desc:
                    current_set_title = html_parser.unescape(current_set['title']['_content'])
                    current_set_title = current_set_title.encode('utf-8') if isinstance(current_set_title, unicode) else current_set_title
                    description_update_args = self.args.copy()
                    description_update_args.update({
                        'photoset_id': current_set['id'],
                        'title': current_set_title,
                        'description': current_set_title
                    })
                    logger.info('Updating set with no description to [%s].' % current_set_title)
                    json.loads(self.api.photosets_editMeta(**description_update_args))
                    logger.info('Done.')
                    desc = current_set_title

                if desc:
                    self.photo_sets_map[desc] = current_set['id']
                    title = self.get_custom_set_title(self.cmd_args.sync_path + desc)
                    if self.cmd_args.update_custom_set and title != current_set['title']['_content']:
                        update_args = self.args.copy()
                        update_args.update({
                            'photoset_id': current_set['id'],
                            'title': title,
                            'description': desc
                        })
                        logger.info('Updating custom title to [%s].' % title)
                        json.loads(self.api.photosets_editMeta(**update_args))
                        logger.info('Done.')

    def upload(self, file_path, photo, folder):
        upload_args = {
            # (optional) Title of the photo
            'title': photo,
            # (optional) Description of the photo (may contain some limited HTML)
            'description': folder,
            # (optional) Specify who can view the photo (set 0 for no, 1 for yes)
            'is_public': 0,
            'is_friend': 0,
            'is_family': 0,
            # (optional) Set to 1 for Safe, 2 for Moderate, or 3 for Restricted
            'safety_level': 1,
            # (optional) Set to 1 for Photo, 2 for Screenshot, or 3 for Other
            'content_type': 1,
            # (optional) Set to 1 to keep the photo in global search results, or 2 to hide from public searches
            'hidden': 2
        }

        for i in range(RETRIES):
            try:
                upload = self.api.upload(file_path, None, **upload_args)
                photo_id = upload.find('photoid').text
                self.add_to_photo_set(photo_id, folder)
                return photo_id
            except Exception as e:
                logger.warning("Retrying upload of [%s/%s] after error: [%s]." % (folder, photo, e))
        logger.error("Failed to upload [%s/%s] after %d retries." % (folder, photo, RETRIES))

    def download(self, url, path):
        folder = os.path.dirname(path)
        if not os.path.isdir(folder):
            os.makedirs(folder)   
        for i in range(RETRIES):
            try:
                return urllib.urlretrieve(url, path)
            except Exception as e:
                logger.warning("Retrying download of [%s] after error: [%s]." % (path, e))
        # Failed too many times
        logger.error("Failed to download [%s] after %d retries." % (path, RETRIES))

