#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  load_lexicon.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

from os import path
from xml.etree import cElementTree as ElementTree

from cjktools.common import sopen
import consoleLog

from lexicon import models
import settings

log = consoleLog.default
_jmDictPath = path.join(settings.DATA_DIR, 'JMdict.gz')

#----------------------------------------------------------------------------#

def load_lexicon(filename=_jmDictPath):
    """
    Reloads the lexicon into the database.
    """
    log.start('Rebuilding the lexicon', nSteps=3)
    log.log('Clearing the database')
    models.Lexeme.objects.all().delete()

    log.start('Loading JMdict', nSteps=2)
    
    log.log('Reading from %s' % path.basename(filename))
    iStream = sopen(filename, 'r', 'byte')
    data = iStream.read()
    iStream.close()
    
    log.log('Parsing XML tree')
    tree = ElementTree.fromstring(data)
    del data
    log.finish()
    
    log.log('Storing lexemes', newLine=False)
    for lexeme in consoleLog.withProgress(tree.getchildren(), 100):
        _store_lexeme(lexeme)
    log.finish()

#----------------------------------------------------------------------------#

def _store_lexeme(lexeme_node):
    surface_list = [n.find('keb').text for n in lexeme_node.findall('k_ele')]
    reading_list = [n.find('reb').text for n in lexeme_node.findall('r_ele')]
    sense_list = lexeme_node.findall('sense')
    
    if not (reading_list and sense_list):
        print "Warning: lexeme is missing crucial data"
        return
    
    # Without kanji elements, the reading elements become the surface
    # elements.
    if not surface_list:
        surface_list = reading_list
    
    lexeme = models.Lexeme()
    lexeme.save()
    
    for surface in surface_list:
        lexeme.surface_set.create(surface=surface)
    
    for reading in reading_list:
        lexeme.reading_set.create(reading=reading)

    for sense in sense_list:
        for gloss in sense.findall('gloss'):
            code_keys = [key for key in gloss.keys() if key.endswith('lang')]
            if code_keys:
                (code_key,) = code_keys
                language_code = gloss.get(code_key)
            else:
                language_code = 'eng'
            language = _get_language(language_code)
            lexeme.sense_set.create(gloss=gloss.text,
                    language=language)
    return

_known_languages = {}
def _get_language(language_code):
    """
    Fetches or creates the database object for a language, caching it in
    memory to reduce database queries.
    """
    global _known_languages
    try:
        return _known_languages[language_code]
    except KeyError:
        language = models.Language.objects.get_or_create(
                code=language_code)[0]
        _known_languages[language_code] = language
        return language

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    load_lexicon()