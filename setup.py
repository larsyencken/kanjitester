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

from setuptools import setup, find_packages, Extension

setup(
        name='kanji_test',
        version='0.1a',
        description='Kanji testing framework',
        author='Lars Yencken',
        author_email='lljy@csse.unimelb.edu.au',
        license='GPL',
        url='http://www.csse.unimelb.edu.au/~lljy/',

        packages=find_packages(),
        ext_modules=[Extension(
                'kanji_test/plugins/visual_similarity/metrics/stroke',
                ['kanji_test/plugins/visual_similarity/metrics/stroke.pyx'],
            )],
    )

# vim: ts=4 sw=4 sts=4 et tw=78: