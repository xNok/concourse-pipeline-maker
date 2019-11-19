#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='cpm',
      version='1.3.0',
      description='Generate pipelines_file to be used with concourse/concourse-pipeline-resource',
      author='Alexandre Couedelo',
      author_email='alexandre.couedelo@desjardins.com',
      packages=find_packages(exclude=['docs', 'tests*']),
      entry_points = {
        'console_scripts': [
            'cpm=cli_cpm.cli:main'
        ],
      }
     )
