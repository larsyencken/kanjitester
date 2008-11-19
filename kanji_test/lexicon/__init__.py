# -*- coding: utf-8 -*-
# 
#  __init__.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

"""
An application which provides basic and exact lexical access.
"""

# Dependencies
from kanji_test import util as _requires_util
import checksum as _requires_checksum

def build():
    import load_lexicon
    load_lexicon.load_lexicon()
