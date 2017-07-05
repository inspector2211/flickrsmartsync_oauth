# flickrsmartsync_oauth

Upload, download or sync photos and videos to flickr.

## Install

Download flickrsmartsync_oauth:
  git clone https://github.com/inspector2211/flickrsmartsync_oauth

Create your own personal Flickr API keys:
  https://www.flickr.com/services/apps/create/apply

Add api_key and api_secret to flickrsmartsync_oauth/flickrsmartsync_oauth/config.py:
  api_key = u'<API_KEY>'
  api_secret = u'<API_SECRET>'

Run the install script:
  python setup.py install

## Example Usage

Upload all photos and vidoes in current folder and all sub-folders:
  flickrsmartsync_oauth

## Acknowledgments

flickrsmartsync_oauth is an extension of [flickrsmartsync](https://github.com/faisalraja/flickrsmartsync) written by Faisal Raja.
flickrsmartsync_oauth includes [flickrapi](https://github.com/sybrenstuvel/flickrapi) version 2.3 supporting oauth written by Sybren Stuvel.

## License

MIT
