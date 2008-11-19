# -*- coding: utf-8 -*-
# 
#  __init__.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

"""
A generic drill tutor which relies on other applications providing methods to generate drill questions.
"""

# Package dependencies
from kanji_test import user_model as _requires_user_model
from kanji_test import drill as _requires_drill
from kanji_test import util as _requires_util
from kanji_test import user_profile as _requires_user_profile
