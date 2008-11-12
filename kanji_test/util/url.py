# -*- coding: utf-8 -*-
#
#  url.py
#  kanji_test
# 
#  Created by Lars Yencken on 13-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Convenience methods for working with urls. Borrowed from:

    http://www.djangosnippets.org/snippets/1159/
"""

# vim: ts=4 sw=4 sts=4 et tw=78:

from django.utils.http import urlquote  as django_urlquote
from django.utils.http import urlencode as django_urlencode
from django.utils.datastructures import MultiValueDict

def urlquote(link=None, get={}):
    u'''
    This method does both: urlquote() and urlencode()

    urlqoute(): Quote special characters in 'link'

    urlencode(): Map dictionary to query string key=value&...

    HTML escaping is not done.

    Example:

      urlquote('/wiki/Python_(programming_language)')     --> '/wiki/Python_%28programming_language%29'
      urlquote('/mypath/', {'key': 'value'})              --> '/mypath/?key=value'
      urlquote('/mypath/', {'key': ['value1', 'value2']}) --> '/mypath/?key=value1&key=value2'
      urlquote({'key': ['value1', 'value2']})             --> 'key=value1&key=value2'
    '''
    if not (link or get):
        raise ValueError('need link or get values')

    if isinstance(link, dict):
        # urlqoute({'key': 'value', 'key2': 'value2'}) --> key=value&key2=value2
        assert not get, get
        get=link
        link=''
    assert isinstance(get, dict), 'wrong type "%s", dict required' % type(get)
    assert not (link.startswith('http://') or link.startswith('https://')), \
        'This method should only quote the url path. It should not start with http(s)://  (%s)' % (
        link)
    if get:
        # http://code.djangoproject.com/ticket/9089
        if isinstance(get, MultiValueDict):
            get=get.lists()
        if link:
            link='%s?' % django_urlquote(link)
        return u'%s%s' % (link, django_urlencode(get, doseq=True))
    else:
        return django_urlquote(link)
