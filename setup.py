#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import sys
from setuptools import setup, find_packages

with open('README.md') as readme_file:   readme = readme_file.read()

def to_list(buffer): return list(filter(None, map(str.strip, buffer.splitlines())))

requirements = to_list("""
    click
    icrawler
    Pillow
    piexif
    tqdm
""")

setup(
    name = 'fastclass',
    version = '0.1.3',
    packages = find_packages(),
    install_requires = requirements,
    python_requires  = '>=3.6',

    description = "small tools to download and evaluate images for deep learning",
    long_description = readme,
    long_description_content_type = 'text/markdown',
    keywords = 'deep learning, crawler, preprocessing',

    license = "Apache Software License 2.0",

    url = 'https://github.com/cwerner/fastclass',

    author = "Christian Werner",
    author_email = 'cwerner.gh@gmail.com',

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    entry_points={
        'console_scripts': [
            'fcc=fastclass.fc_clean:cli',
            'fcd=fastclass.fc_download:cli',
        ],
    },

    zip_safe = False,
)
