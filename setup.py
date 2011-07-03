#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py
#  kanji_test
# 
#  Created by Lars Yencken on 18-09-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Build script for the kanji_test project.
"""

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages, Extension
import os
from os import path

def get_revision():
    revision = None
    if os.system('which hg >/dev/null 2>&1') == 0:
        revision = os.popen('hg id -n 2>/dev/null').read().strip().rstrip('+')
    return revision or 'unknown'

setup(
        name='kanji_test',
        version='1.4',
        description='Kanji testing framework',
        author='Lars Yencken',
        author_email='lars@yencken.org',
        license='GPL',
        url='http://kanjitester.gakusha.info/',

        setup_requires=['setuptools_hg'],
        install_requires=[
            'django >= 1.0',
            'consoleLog',
            'cjktools >= 1.3.0',
            'cjktools_data',
            'mysql-python',
            'south',
            'django-checksum',
            'pyyaml',
            'nltk',
        ],

        packages=find_packages(),
        ext_modules=[Extension(
                path.join('kanji_test', 'plugins',
                    'visual_similarity', 'metrics', 'stroke'),
                [path.join('kanji_test', 'plugins',
                    'visual_similarity', 'metrics', 'stroke.pyx')]
            )],
        include_package_data=True,
    )

# vim: ts=4 sw=4 sts=4 et tw=78:
