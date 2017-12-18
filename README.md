# flickrsmartsync_oauth

Upload, download or sync photos and videos to Flickr.

## Install

Download flickrsmartsync_oauth:

```sh
> git clone https://github.com/inspector2211/flickrsmartsync_oauth
```

Create your own personal Flickr API keys:

```sh
  1. To use this script, you must apply for your own private Flickr API keys
  2. Visit URL
     https://www.flickr.com/services/api/misc.api_keys.html
  3. Apply for your key online
  4. Apply for a non-commercial key
  5. Store your API keys in a file named config.py with the following format
     api_key = 'key'
     api_secret = 'secret'
```

Run the install script:
```sh
> python setup.py install
```

## Example Usage

Upload all photos and vidoes in current folder and all sub-folders:

```sh
> flickrsmartsync_oauth
```

## Acknowledgments

flickrsmartsync_oauth is an extension of [flickrsmartsync](https://github.com/faisalraja/flickrsmartsync) written by Faisal Raja.
flickrsmartsync_oauth includes [flickrapi](https://github.com/sybrenstuvel/flickrapi) version 2.3 supporting oauth written by Sybren Stuvel.

## License

MIT
