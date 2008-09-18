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

import load_lexicon

def build():
    load_lexicon.load_lexicon()