#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='cpm',
      version='1.2.7',
      description='Generate pipelines_file to be used with concourse/concourse-pipeline-resource',
      author='Alexandre Couedelo',
      author_email='alexandre.couedelo@desjardins.com',
      packages=find_packages(exclude=['docs', 'tests*']),
      entry_points = {
        'console_scripts': [
            'cpm=cpm_cli.cli_maker:main'
        ],
      }
     )
