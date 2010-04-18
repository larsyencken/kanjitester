# -*- coding: utf-8 -*-
#
#  lang_middleware.py
#  kanji_test
# 
#  Created by Lars Yencken on 18-04-2010.
#  Copyright 2010 Lars Yencken. All rights reserved.
#

"""
"""

from cjktools import scripts

class TagLanguageMiddleware(object):
    def __init__(self):
        self.japanese_scripts = set([
                scripts.Script.Katakana,
                scripts.Script.Hiragana,
                scripts.Script.Kanji,
            ])

    def process_response(self, request, response):
        if response.status_code != 200:
            return response

        if not response.get('Content-Type', '').startswith('text/html'):
            return response

        content = response.content.decode('utf8')
        if not scripts.script_types(content).intersection(
                    self.japanese_scripts):
            return response

        parts = []
        for part in scripts.script_boundaries(content):
            if scripts.script_type(part) in self.japanese_scripts:
                parts.append('<span lang="ja" xml:lang="ja">%s</span>' % part)
            else:
                parts.append(part)

        response.content = u''.join(parts).encode('utf8')

        return response

# vim: ts=4 sw=4 sts=4 et tw=78:

