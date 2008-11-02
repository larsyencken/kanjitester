#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  add_syllabus.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-22.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import os, sys, optparse
import re
import glob

from cjktools.common import sopen
from cjktools import scripts
import consoleLog

from kanji_test.lexicon import models as lexicon_models
from kanji_test.user_model import models as usermodel_models
from kanji_test import settings

#----------------------------------------------------------------------------#

_log = consoleLog.default
_syllabi_path = os.path.join(settings.DATA_DIR, 'syllabus')

#----------------------------------------------------------------------------#

def list_syllabi():
    syllabi = _fetch_syllabi()
    _log.start('Available syllabi', nSteps=len(syllabi))
    for syllabus_name in syllabi:
        _log.log(syllabus_name)
    _log.finish()

def add_all_syllabi():
    syllabi = _fetch_syllabi()
    _log.start('Adding all syllabi', nSteps=len(syllabi))
    for syllabus_name in syllabi:
        add_syllabus(syllabus_name)
    _log.finish()

def add_syllabus(syllabus_name):
    """Adds the given syllabus to the database interactively."""
    word_filename, char_filename = _check_syllabus_name(syllabus_name)
    tag = syllabus_name.replace('_', ' ')
    _log.start('Adding syllabus %s' % tag, nSteps=5)

    _log.log('Clearing any existing objects')    
    usermodel_models.Syllabus.objects.filter(tag=tag).delete()
    
    _log.log('Creating new syllabus object')
    syllabus = usermodel_models.Syllabus(tag=tag)
    syllabus.save()
    
    _log.start('Parsing word list')
    n_ok = 0
    skipped = []
    for reading, surface, disambiguation in SyllabusParser(word_filename):
        lexeme = _find_matching_lexeme(reading, surface, skipped,
                disambiguation)
        if not lexeme:
            continue
        partial_lexeme = syllabus.partiallexeme_set.get_or_create(
                lexeme=lexeme)[0]
        partial_lexeme.reading_set.add(lexeme.reading_set.get(reading=reading))
        if disambiguation:
            partial_lexeme.sensenote_set.create(note=disambiguation)
        n_ok += 1
    _log.log('%d ok, %d skipped (see skipped.log)' % (n_ok, len(skipped)))
    _log.finish()

    o_stream = sopen('skipped.log', 'w')
    print >> o_stream, "# vim: set ts=20 noet sts=20:"
    for skipped_word in skipped:
        print >> o_stream, skipped_word
    o_stream.close()
    
    _log.log('Parsing kanji list')
    i_stream = sopen(char_filename)
    kanji_set = scripts.uniqueKanji(i_stream.read())
    for kanji in kanji_set:
        syllabus.partialkanji_set.create(kanji_id=kanji)
    i_stream.close()

    _log.log('Building lexeme surfaces from kanji')
    for partial_lexeme in syllabus.partiallexeme_set.all():
        for lexeme_surface in partial_lexeme.lexeme.surface_set.all():
            if scripts.uniqueKanji(lexeme_surface.surface).issubset(
                    kanji_set):
                partial_lexeme.surface_set.add(lexeme_surface)

    _log.finish()

#----------------------------------------------------------------------------#

def _fetch_syllabi():
    syllabi = []
    glob_pattern = os.path.join(_syllabi_path, '*.words')
    for word_filename in glob.glob(glob_pattern):
        syllabus_path = os.path.splitext(word_filename)[0]
        if os.path.exists(syllabus_path + '.chars'):
            syllabi.append(os.path.basename(syllabus_path))

    return syllabi

def _check_syllabus_name(syllabus_name):
    word_filename = os.path.join(_syllabi_path, syllabus_name + '.words')
    char_filename = os.path.join(_syllabi_path, syllabus_name + '.chars')
    if not os.path.exists(word_filename) or \
            not os.path.exists(char_filename):
        print >> sys.stderr, "Can't find syllabus matching %s" % syllabus_name
        sys.exit(1)
    return word_filename, char_filename

def _find_matching_lexeme(reading, surface=None, skipped=None, 
        disambiguation=None):
    """Finds a uniquely matching lexeme for this specification."""    
    if skipped is None:
        skipped = []
    
    matches = set(
        [r.lexeme for r in lexicon_models.LexemeReading.objects.filter(
                reading=reading)]
    )
    if surface:
        matches = matches.intersection(
                [s.lexeme for s in lexicon_models.LexemeSurface.objects.filter(
                        surface=surface)]
            )
    if len(matches) == 0:
        skipped.append(u'%s\t%s\t%s\tno match' % (
                reading,
                surface or '',
                disambiguation or '',
            ))
        return None
    elif len(matches) > 1:
        skipped.append(u'%s\t%s\t%s\ttoo many matches' % (
                reading,
                surface or '',
                disambiguation or '',
            ))
        return None
    
    (unique_match,) = list(matches)
    return unique_match
    
#----------------------------------------------------------------------------#

class SyllabusParser(object):
    """Parses files in the standard syllabus format."""
    def __init__(self, filename):
        self.filename = filename
        self.i_stream = sopen(filename)
        self.kanji = set()
    
    def __iter__(self):
        for line in self.i_stream:
            if line.startswith(u'#'):
                continue
            line = line.rstrip()
            if u'〜' in line:
                line = line.replace(u'〜', u'')
            if u'・' in line:
                yield self._parse_line(line.replace(u'・', ''))
                yield self._parse_line(
                        re.subn(u'・[^ \t]*', '', line, re.UNICODE)[0])
            else:
                yield self._parse_line(line)        
    
    def _parse_line(self, line):
        """Splits the line into a reading and possibly extra information."""
        parts = line.rstrip().split()
        reading = parts.pop(0)
        surface = None
        disambiguation = None
        
        num_parts = len(parts)
        if num_parts == 2:
            disambiguation = parts.pop().strip('[]')
            surface = parts.pop()
        
        elif num_parts == 1:
            last_part = parts.pop()
            if not last_part.startswith(u'['):
                surface = last_part
                return reading, surface, disambiguation
            
            disambiguation = last_part.strip('[]')
        elif num_parts != 0:
            raise Exception('format error: bad number of parts')
        
        # No surface string => kana entry
        return reading, surface, disambiguation
    
    def __del__(self):
        self.i_stream.close()
        
#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [-la] [syllabus]

Installs the priors for a syllabus. Use the -l option to check what's
available, or -a to just install them all."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            help='Enables debugging mode [False]')

    parser.add_option('-l', '--list', action='store_true', dest='list_syllabi',
            help='List the available syllabi.')

    parser.add_option('-a', '--all', action='store_true', dest='all',
            help='Install all available syllabi.')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if options.list_syllabi:
        list_syllabi()

    elif options.all:
        add_all_syllabi()

    elif len(args) == 1:
        syllabus_name = args[0]
        add_syllabus(syllabus_name)

    else:
        parser.print_help()
        sys.exit(1)

    return

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
