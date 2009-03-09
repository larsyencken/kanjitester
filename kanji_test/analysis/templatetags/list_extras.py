# -*- coding: utf-8 -*-
# 
#  list_extras.py
#  kanji_test
#  
#  Created by Lars Yencken on 2009-03-09.
#  Copyright 2009 Lars Yencken. All rights reserved.
# 

"""
Extra filters for working with lists of data.
"""

from django import template

register = template.Library()

@register.filter
def first_n(values, n):
    "Returns the first n items of a list."
    if type(values) != list or type(n) != int or n < 0:
        return values

    return values[:n]
    