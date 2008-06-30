# -*- coding: utf-8 -*-
# 
#  tests.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-30.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from os import path
import unittest

from cjktools import dyntest
from django.test import TestCase

def suite():
    """Generates a test suite for this package."""
    return unittest.TestSuite((
            _dynamic_suite(),
        ))

def _dynamic_suite():
    current_dir = path.dirname(__file__)
    return dyntest.dynamicSuite(
            current_dir,
            excludes=[
                    # This module, to avoid infinite recursion.
                    __file__.rstrip('c'),
                    # The models module, which django tests already.
                    path.join(current_dir, 'models.py'),
                ],
            baseImportPath=['lexicon'],
        )
