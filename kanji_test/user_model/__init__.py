# -*- coding: utf-8 -*-
# 
#  __init__.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-24.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

"""
All aspects of user proficiency and error modeling.
"""

# Dependencies
from kanji_test import util as _requires_util
from kanji_test import lexicon as _requires_lexicon
import checksum as _requires_checksum

def build():
    import add_syllabus
    add_syllabus.add_all_syllabi()
