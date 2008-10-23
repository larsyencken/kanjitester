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

from cjktools.common import sopen
from cjktools import scripts

from kanji_test.lexicon import models as lexicon_models
from kanji_test.drill_tutor import models as drilltutor_models

def add_syllabus(tag, filename):
    """Adds the given syllabus to the database interactively."""
    if drilltutor_models.Syllabus.objects.filter(tag=tag).count() > 0:
        if not ask_yes_no("Overwrite existing syllabus tagged %s?" % tag):
            return
        print 'Deleting old syllabus'
        drilltutor_models.Syllabus.objects.filter(tag=tag).delete()
    
    print 'Creating syllabus %s' % tag
    syllabus = drilltutor_models.Syllabus(tag=tag)
    syllabus.save()
    
    print 'Parsing syllabus file'
    i_stream = sopen(filename)
    for line in i_stream:
        if line.startswith('#'):
            continue
            
        reading, surface, disambiguation = _parse_line(line)
        if disambiguation:
            print 'Skipping %s [%s]' % (reading, disambiguation)
            continue
        lexeme = _find_matching_lexeme(reading, surface)
        if not lexeme:
            continue
        partial_lexeme = drilltutor_models.PartialLexeme(
                lexeme=lexeme)
        partial_lexeme.save()
        syllabus.partial_lexemes.add(partial_lexeme)
        
    i_stream.close()

def _find_matching_lexeme(reading, surface=None):
    """Finds a uniquely matching lexeme for this specification."""
    if not surface:
        surface = reading

    matches = set(
        [s.lexeme for s in lexicon_models.LexemeSurface.objects.filter(
                surface=surface)]
    ).intersection(
        [r.lexeme for r in lexicon_models.LexemeReading.objects.filter(
                reading=reading)]
    )
    if not matches:
        print u'No match for %s /%s/' % (surface or reading, surface)
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
            line = line.rstrip()
            if u'・' in line:
                yield self._parse_line(line.replace(u'・', ''))
                yield self._parse_line(
                        re.subn(u'・[^ \t]*', '', line, re.UNICODE))
            else:
                yield self._parse_line(line)        
    
    def _parse_line(self, line):
        """Splits the line into a reading and possibly extra information."""
        parts = line.rstrip().split()
        reading = parts.pop(0)
        surface = None
        disambiguation = None
        reading_scripts = scripts.scriptTypes(reading)
        
        if reading_scripts == set([scripts.Script.Katakana]):
            surface = reading
            reading = scripts.toHiragana(reading)
        elif scripts.Script.Kanji in reading_scripts:
            assert scripts.scriptTypes(reading) == \
                    set([scripts.Script.Hiragana])
            if len(parts) == 2:
                surface = parts[0]
                disambiguation = parts[1]
            else:
                last_part = parts[0]
                if last_part.startswith(u'['):
                    disambiguation = last_part
                else:
                    surface = last_part

        return reading, surface, disambiguation
    
    def __del__(self):
        self.i_stream.close()
        

def main():
    try:
        [tag, filename] = sys.argv[1:]
    except ValueError:
        print 'Usage: add_syllabus.py tag filename'
        return
    
    if not os.path.exists(filename):
        print 'Error: file %s does not exist or is not readable' % filename
        return
        
    add_syllabus(tag, filename)

if __name__ == '__main__':
    main()