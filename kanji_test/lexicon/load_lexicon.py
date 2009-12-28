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
from simplestats.sequences import groups_of_n_iter
from cjktools.common import sopen
from cjktools import scripts
import consoleLog
from checksum.models import Checksum

from kanji_test.lexicon import models
from kanji_test import settings

log = consoleLog.default
_jmdict_path = path.join(settings.DATA_DIR, 'JMdict.gz')
_dependencies = [__file__, models]
_checksum_tag = 'lexicon'

#----------------------------------------------------------------------------#

def load_lexicon(filename=_jmdict_path):
    " Reloads the lexicon into the database."
    log.start('Rebuilding the lexicon', nSteps=5)
    if not Checksum.needs_update(_checksum_tag, _dependencies + [filename]):
        log.finish('Already up-to-date')
        return

    log.log('Loading probability distributions')
    models.initialise()
    
    log.start('Loading JMdict', nSteps=2)
    _clear_lexicon()
    log.log('Reading from %s' % path.basename(filename))
    iStream = sopen(filename, 'r', 'byte')
    data = iStream.read()
    iStream.close()
    log.log('Parsing XML tree')
    tree = ElementTree.fromstring(data)
    del data
    log.finish()
    
    _store_lexemes(tree.getchildren())

    log.log('Storing checksum')
    Checksum.store(_checksum_tag, _dependencies + [filename])
    
    log.finish()

#----------------------------------------------------------------------------#

def _clear_lexicon():
    cursor = connection.cursor()
    tables = [
            'lexicon_lexemesurface',
            'lexicon_lexemesense',
            'lexicon_lexemereading',
            'lexicon_lexeme',
        ]
    try:
        for table_name in tables:
            cursor.execute('DELETE FROM %s' % table_name)
            cursor.execute('COMMIT')
    except:
        models.Lexeme.objects.all().delete()
    return

#----------------------------------------------------------------------------#

def _populate_stacks(lexeme_node, lexeme_id, lexeme_surface_stack,
        lexeme_sense_stack, lexeme_reading_stack):
    surface_set = set(n.find('keb').text.upper() for n in \
            lexeme_node.findall('k_ele'))
    reading_list = [n.find('reb').text for n in \
            lexeme_node.findall('r_ele')]
    sense_list = lexeme_node.findall('sense')

    if not (reading_list and sense_list):
        print "Warning: lexeme is missing crucial data"
        return

    # If we have no kanji, the kana becomes the surface form
    if not surface_set:
        surface_set = set(reading_list)

    in_lexicon = True # All these surfaces are from the original lexicon
    for surface in sorted(surface_set):
        lexeme_surface_stack.append((
                lexeme_id,
                surface.upper(),
                scripts.contains_script(scripts.Script.Kanji, surface),
                in_lexicon,
            ))
    
    for reading in reading_list:
        lexeme_reading_stack.append((lexeme_id, reading))

    is_first_sense = True
    for sense_node in sense_list:
        for gloss in sense_node.findall('gloss'):
            (lang_key,) = [key for key in gloss.keys() if key.endswith('lang')]
            lang = gloss.get(lang_key)
            if lang != 'eng':
                continue
            lexeme_sense_stack.append((lexeme_id, gloss.text, is_first_sense))
            is_first_sense = False
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
    cursor.execute('COMMIT')

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
    for lexeme_rows in groups_of_n_iter(max_rows, xrange(1, next_lexeme_id)):
        cursor.executemany('INSERT INTO lexicon_lexeme (id) VALUES (%s)',
                lexeme_rows)

    log.log('Storing to lexicon_lexemesurface')
    for lexeme_surface_rows in groups_of_n_iter(max_rows, lexeme_surface_stack):
        cursor.executemany( """
                INSERT INTO lexicon_lexemesurface (lexeme_id, surface,
                    has_kanji, in_lexicon)
                VALUES (%s, %s, %s, %s)
            """, lexeme_surface_rows)

    log.log('Storing to lexicon_lexemereading')
    for lexeme_reading_rows in groups_of_n_iter(max_rows, lexeme_reading_stack):
        cursor.executemany( """
                INSERT INTO lexicon_lexemereading (lexeme_id, reading)
                VALUES (%s, %s)
            """, lexeme_reading_rows)

    log.log('Storing to lexicon_lexemesense')
    for lexeme_sense_rows in groups_of_n_iter(max_rows, lexeme_sense_stack):
        cursor.executemany( """
                INSERT INTO lexicon_lexemesense (lexeme_id, gloss,
                        is_first_sense)
                VALUES (%s, %s, %s)
            """, lexeme_sense_rows)

    connection._commit()
    log.finish()
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    load_lexicon()

