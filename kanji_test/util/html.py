# -*- coding: utf-8 -*-
# 
#  html.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

"""
Helper methods for constructing html, inspired by MochiKit.

>>> P('dog')
'<p>dog</p>'

>>> INPUT(value='Enter dog name', type='text', name="dog_name")
'<input type="text" name="dog_name" value="Enter dog name"></input>'

>>> TABLE(THEAD(TR(TH('Header'))), TBODY())
'<table><thead><tr><th>Header</th></tr></thead> <tbody></tbody></table>'
"""

def _makeTagFunction(tag):
    def f(*children, **attribs):
        return '<%s%s>%s</%s>' % (
                tag,
                _fromAttribs(**attribs),
                ' '.join(children),
                tag,
            )
    f.__name__ = tag.upper()
    return f
            
def _fromAttribs(**attribs):
    results = ['']
    for key, value in attribs.iteritems():
        results.append('%s="%s"' % (key, value))
    return ' '.join(results)

_tags = ['p', 'td', 'tr', 'th', 'table', 'em', 'thead', 'tbody', 'br', 'ul',
    'ol', 'li', 'input', 'form', 'div', 'span']
    
for tag in _tags:
    globals()[tag.upper()] = _makeTagFunction(tag)