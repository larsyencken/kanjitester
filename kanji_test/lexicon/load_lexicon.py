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

from django.db import connection
from cjktools.common import sopen
from cjktools.sequences import groupsOfNIter
from cjktools import scripts
import consoleLog
from nltk.probability import FreqDist

from kanji_test.lexicon import models
from kanji_test import settings

log = consoleLog.default
_jmdict_path = path.join(settings.DATA_DIR, 'JMdict.gz')

#----------------------------------------------------------------------------#

def load_lexicon(filename=_jmdict_path):
    " Reloads the lexicon into the database."
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
    
    _store_lexemes(tree.getchildren())
    
    log.finish()

#----------------------------------------------------------------------------#

def _populate_stacks(lexeme_node, lexeme_id, lexeme_surface_stack,
        lexeme_sense_stack, lexeme_reading_stack):
    surface_list = [n.find('keb').text for n in \
            lexeme_node.findall('k_ele')]
    reading_list = [n.find('reb').text for n in \
            lexeme_node.findall('r_ele')]
    sense_list = lexeme_node.findall('sense')

    if not (reading_list and sense_list):
        print "Warning: lexeme is missing crucial data"
        return

    # If we have no kanji, the kana becomes the surface form
    if not surface_list:
        surface_list = reading_list

    in_lexicon = True # All these surfaces are from the original lexicon
    for surface in surface_list:
        lexeme_surface_stack.append((
                lexeme_id,
                surface,
                scripts.containsScript(scripts.Script.Kanji, surface),
                in_lexicon,
            ))
    
    for reading in reading_list:
        lexeme_reading_stack.append((lexeme_id, reading))

    for sense_node in sense_list:
        for gloss in sense_node.findall('gloss'):
            code_keys = [key for key in gloss.keys() if key.endswith('lang')]
            if code_keys:
                (code_key,) = code_keys
                language_code = gloss.get(code_key)
            else:
                language_code = 'eng'
            language = _get_language(language_code)
            lexeme_sense_stack.append((lexeme_id, gloss.text, language.code))
    return

#----------------------------------------------------------------------------#

def _store_lexemes(lexeme_nodes):
    log.start('Storing lexemes', nSteps=6)
    cursor = connection.cursor()

    log.log('Clearing tables')
    cursor.execute('DELETE FROM lexicon_lexemereading')
    cursor.execute('DELETE FROM lexicon_lexemesense')
    cursor.execute('DELETE FROM lexicon_lexemesurface')
    cursor.execute('DELETE FROM lexicon_lexeme')

    next_lexeme_id = 1
    lexeme_surface_stack = []
    lexeme_sense_stack = []
    lexeme_reading_stack = []

    log.log('Building insert stacks')
    for lexeme_node in lexeme_nodes:
        _populate_stacks(lexeme_node, next_lexeme_id, lexeme_surface_stack,
                lexeme_sense_stack, lexeme_reading_stack)
        next_lexeme_id += 1

    max_rows = settings.N_ROWS_PER_INSERT

    log.log('Storing to lexicon_lexeme')
    for lexeme_rows in groupsOfNIter(max_rows, xrange(1, next_lexeme_id)):
        cursor.executemany('INSERT INTO lexicon_lexeme (id) VALUES (%s)',
                lexeme_rows)

    log.log('Storing to lexicon_lexemesurface')
    for lexeme_surface_rows in groupsOfNIter(max_rows, lexeme_surface_stack):
        cursor.executemany( """
                INSERT INTO lexicon_lexemesurface (lexeme_id, surface,
                    has_kanji, in_lexicon)
                VALUES (%s, %s, %s, %s)
            """, lexeme_surface_rows)

    log.log('Storing to lexicon_lexemereading')
    for lexeme_reading_rows in groupsOfNIter(max_rows, lexeme_reading_stack):
        cursor.executemany( """
                INSERT INTO lexicon_lexemereading (lexeme_id, reading)
                VALUES (%s, %s)
            """, lexeme_reading_rows)

    log.log('Storing to lexicon_lexemesense')
    for lexeme_sense_rows in groupsOfNIter(max_rows, lexeme_sense_stack):
        cursor.executemany( """
                INSERT INTO lexicon_lexemesense (lexeme_id, gloss, language_id)
                VALUES (%s, %s, %s)
            """, lexeme_sense_rows)

    connection._commit()
    log.finish()
    return

#----------------------------------------------------------------------------#

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

