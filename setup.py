#! /usr/bin/env python

import os
import sys
from setuptools import setup, find_packages

VERSION = '1.0.0'

def main():
    setup(name='flickrsmartsync_oauth',
          version=VERSION,
          description="Upload, download or sync photos and videos to Flickr",
          long_description=open('README.txt').read(),
          classifiers=[
              'Development Status :: 3 - Alpha',
              'Environment :: Console',
              'Programming Language :: Python',
              'License :: OSI Approved :: MIT License'
          ],
          keywords='flickr upload download sync photos images videos backup',
          url='https://github.com/inspector2211/flickrsmartsync_oauth',
          license='MIT',
          packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
          include_package_data=True,
          zip_safe=False,
          install_requires=['flickrapi', 'IPTCInfo'],
          entry_points={
              "console_scripts": ['flickrsmartsync_oauth = flickrsmartsync_oauth:main'],
          },
          )

if __name__ == '__main__':
    main()
