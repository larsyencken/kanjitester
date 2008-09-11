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
from nltk.probability import FreqDist

from lexicon import models
import settings

log = consoleLog.default
_jmdict_path = path.join(settings.DATA_DIR, 'JMdict.gz')
_word_dist_path = path.join(settings.DATA_DIR, 'corpus',
        'jp_word_corpus_counts.gz')

#----------------------------------------------------------------------------#

def load_lexicon(filename=_jmdict_path):
    """
    Reloads the lexicon into the database.
    """
    log.start('Rebuilding the lexicon', nSteps=3)
    
    log.log('Loading probability distributions')
    models.initialise()
    
    log.start('Loading JMdict', nSteps=2)
    models.Lexeme.objects.all().delete()
    log.log('Reading from %s' % path.basename(filename))
    iStream = sopen(filename, 'r', 'byte')
    data = iStream.read()
    iStream.close()
    log.log('Parsing XML tree')
    tree = ElementTree.fromstring(data)
    del data
    log.finish()
    
    log.log('Storing lexemes', newLine=False)
    for lexeme_node in consoleLog.withProgress(tree.getchildren(), 100):
        lexeme = _store_lexeme(lexeme_node)
    
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

    (gloss_field,) = [f for f in models.Kanji._meta.fields \
            if f.name == 'gloss']
    for sense in sense_list:
        for gloss in sense.findall('gloss'):
            code_keys = [key for key in gloss.keys() if key.endswith('lang')]
            if code_keys:
                (code_key,) = code_keys
                language_code = gloss.get(code_key)
            else:
                language_code = 'eng'
            language = _get_language(language_code)
            # Truncate the gloss to our database size.
            gloss_text = gloss.text[:gloss_field.max_length]
            lexeme.sense_set.create(gloss=gloss_text,
                    language=language)

    return lexeme

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
