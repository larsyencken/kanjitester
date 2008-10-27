#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  add_syllabus.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-22.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import os, sys
import re

from cjktools.common import sopen
from cjktools import scripts
import consoleLog

from kanji_test.lexicon import models as lexicon_models
from kanji_test.user_model import models as usermodel_models

_log = consoleLog.default

def add_syllabus(tag, word_file, kanji_file):
    """Adds the given syllabus to the database interactively."""
    _log.start('Adding syllabus %s' % tag, nSteps=4)

    _log.log('Clearing any existing objects')    
    usermodel_models.Syllabus.objects.filter(tag=tag).delete()
    
    _log.log('Creating new syllabus object')
    syllabus = usermodel_models.Syllabus(tag=tag)
    syllabus.save()
    
    _log.start('Parsing word list')
    n_ok = 0
    skipped = []
    for reading, surface, disambiguation in SyllabusParser(word_file):
        if disambiguation:
            skipped.append('%s [%s]' % (reading, disambiguation))
            continue
        lexeme = _find_matching_lexeme(reading, surface, skipped)
        if not lexeme:
            continue
        partial_lexeme = syllabus.partiallexeme_set.create(lexeme=lexeme)
        partial_lexeme.reading_set.add(lexeme.reading_set.get(reading=reading))
        partial_lexeme.surface_set.add(lexeme.surface_set.get(surface=surface))
        n_ok += 1
    _log.log('%d ok, %d skipped' % (n_ok, len(skipped)))
    _log.finish()
    
    _log.log('Parsing kanji list')
    _log.finish()

def _find_matching_lexeme(reading, surface=None, skipped=None):
    """Finds a uniquely matching lexeme for this specification."""
    if surface is None:
        surface = reading
    
    if skipped is None:
        skipped = []
    
    matches_a = set(
        [s.lexeme for s in lexicon_models.LexemeSurface.objects.filter(
                surface=surface)]
    )
    matches_b = set(
        [r.lexeme for r in lexicon_models.LexemeReading.objects.filter(
                reading=reading)]
    )
    matches = matches_a.intersection(matches_b)
    if not matches:
        skipped.append(u'%s /%s/' % (surface or reading, surface))
        return None
    (unique_match,) = list(matches)
    return unique_match
    
def ask_yes_no(question):
    """Asks a yes/no question, and return True if the answer is yes."""
    answer = raw_input('%s [y] ' % question).strip()
    return (not answer) or answer.startswith('y')

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
        
        if len(parts) == 2:
            disambiguation = parts.pop()
            surface = parts.pop()
            return reading, surface, disambiguation
        
        if len(parts) == 1:
            last_part = parts.pop()
            if not last_part.startswith(u'['):
                surface = last_part
                return reading, surface, disambiguation
            
            disambiguation = last_part
        
        # By now we have no surface string    
        surface = reading
        reading = scripts.toHiragana(reading)
        return reading, surface, disambiguation
    
    def __del__(self):
        self.i_stream.close()
        

def main():
    try:
        [tag, word_file, kanji_file] = sys.argv[1:]
    except ValueError:
        print 'Usage: add_syllabus.py tag wordlist kanjilist'
        return

    for filename in (word_file, kanji_file):
        if not os.path.exists(filename):
            print 'Error: file %s does not exist or is not readable' % filename
            return
        
    add_syllabus(tag, word_file, kanji_file)

if __name__ == '__main__':
    main()