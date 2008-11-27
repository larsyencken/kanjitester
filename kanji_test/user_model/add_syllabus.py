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
from cjktools import alternations
import consoleLog
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist
from checksum.models import Checksum

from kanji_test.lexicon import models as lexicon_models
from kanji_test.user_model import models as usermodel_models
from kanji_test.user_model import plugin_api
from kanji_test.util.alignment import Alignment
from kanji_test import settings

#----------------------------------------------------------------------------#

_log = consoleLog.default
_syllabi_path = os.path.join(settings.DATA_DIR, 'syllabus')
_required_extensions = ('.words', '.chars', '.aligned')

#----------------------------------------------------------------------------#
# ACTIONS
#----------------------------------------------------------------------------#

def list_syllabi():
    syllabi = _fetch_syllabi()
    _log.start('Available syllabi', nSteps=len(syllabi))
    for syllabus_name in syllabi:
        _log.log(syllabus_name)
    _log.finish()

#----------------------------------------------------------------------------#

def add_all_syllabi(force=False):
    syllabi = _fetch_syllabi()
    dependencies = _deps_from_syllabi(syllabi)
    _log.start('Adding all syllabi', nSteps=len(syllabi))
    if not force and not Checksum.needs_update('syllabi', dependencies,
            ['lexicon']):
        _log.finish('Already up-to-date')
        return
        
    for syllabus_name in syllabi:
        add_syllabus(syllabus_name, force=force)
    Checksum.store('syllabi', dependencies)
    _log.finish()

#----------------------------------------------------------------------------#

def add_syllabus(syllabus_name, force=False):
    """Adds the given syllabus to the database."""
    _log.start('Adding syllabus %s' % syllabus_name)

    syllabus_path = _check_syllabus_name(syllabus_name)
    word_file = syllabus_path + '.words'
    char_file = syllabus_path + '.chars'
    aligned_file = syllabus_path + '.aligned'

    syllabus = _init_syllabus(syllabus_name)
    _load_kanji_list(char_file, syllabus)
    _load_word_list(word_file, syllabus)
    _load_aligned_readings(aligned_file, syllabus)

    _log.start('Adding error models')
    plugin_api.load_priors(syllabus, force=force)
    _log.finish()

    _log.finish()

#----------------------------------------------------------------------------#

def add_per_user_models(username):
    _log.log('Initializing error models for user %s' % username)
    user = auth_models.User.objects.get(username=username)
    usermodel_models.ErrorDist.init_from_priors(user)

#----------------------------------------------------------------------------#
# PRIVATE
#----------------------------------------------------------------------------#

def _init_syllabus(syllabus_name):
    _log.start('Initialising syllabus %s' % syllabus_name, nSteps=2)
    tag = syllabus_name.replace('_', ' ')
    _log.log('Clearing any existing objects')    
    usermodel_models.Syllabus.objects.filter(tag=tag).delete()
    
    _log.log('Creating new syllabus object')
    syllabus = usermodel_models.Syllabus(tag=tag)
    syllabus.save()
    _log.finish()
    return syllabus

def _load_aligned_readings(aligned_file, syllabus):
    _log.start('Determining readings from alignments', nSteps=3)
    alignments = _load_alignments(aligned_file)
    _load_kanji_readings(alignments, syllabus)
    _determine_word_surfaces(alignments, syllabus)
    _log.finish()
    
def _fetch_syllabi():
    syllabi = []
    glob_pattern = os.path.join(_syllabi_path, '*' + _required_extensions[0])
    for word_filename in glob.glob(glob_pattern):
        syllabus_path = os.path.splitext(word_filename)[0]
        for extension in _required_extensions:
            if not os.path.exists(syllabus_path + extension):
                break
        else:
            syllabi.append(os.path.basename(syllabus_path))

    return syllabi

def _deps_from_syllabi(syllabi):
    "Returns a list of build dependencies given the syllabi names."
    dependencies = [__file__, plugin_api]
    for syllabus_name in syllabi:
        syllabus_path = _check_syllabus_name(syllabus_name)
        for extension in _required_extensions:    
            dependencies.append(syllabus_path + extension)

    return dependencies

def _load_alignments(aligned_file):
    _log.log('Loading alignments')
    i_stream = sopen(aligned_file)
    alignments = []
    for line in i_stream:
        alignment = Alignment.from_line(line)
        alignments.append(alignment)
    i_stream.close()
    return alignments

def _check_syllabus_name(syllabus_name):
    syllabus_path = os.path.join(_syllabi_path, syllabus_name)
    for extension in ('.words', '.chars', '.aligned'):
        syllabus_file = syllabus_path + extension
        if not os.path.exists(syllabus_file):
            print >> sys.stderr, "Can't find syllabus file %s" % syllabus_file
            sys.exit(1)
    return syllabus_path

def _find_matching_lexeme(reading, surface='', skipped=None, 
        disambiguation=''):
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

def _determine_word_surfaces(alignments, syllabus):
    """
    Aligns the word surfaces with JMdict. We also use our known kanji set,
    replacing any unknown kanji with their readings. If this results in a
    surface known to JMdict, then we add that surface to the lexeme's list.
    """
    _log.start('Building lexeme surfaces from kanji', nSteps=3)

    _log.log('Loading kanji set')
    kanji_set = set(o.kanji for o in lexicon_models.Kanji.objects.filter(
            partialkanji__syllabus=syllabus))

    _add_reduced_surfaces(alignments, kanji_set, syllabus)

    _log.log('Adding existing surfaces')
    for partial_lexeme in syllabus.partiallexeme_set.all():
        if partial_lexeme.surface_set.count() == 0:
            for lexeme_surface in partial_lexeme.lexeme.surface_set.all():
                if scripts.uniqueKanji(lexeme_surface.surface).issubset(
                        kanji_set):
                    partial_lexeme.surface_set.add(lexeme_surface)

    _log.finish()

#----------------------------------------------------------------------------#

def _add_reduced_surfaces(alignments, kanji_set, syllabus):
    _log.start('Adding reduced surfaces where needed', nSteps=1)
    n_reduced = 0

    for alignment in alignments:
        if not scripts.containsScript(scripts.Script.Kanji,
                alignment.grapheme):
            continue

        partial_lexeme = syllabus.partiallexeme_set.filter(
                lexeme__reading_set__reading=alignment.phoneme
            ).get(
                lexeme__surface_set__surface=alignment.grapheme
            )
        lexeme_surface = partial_lexeme.lexeme.surface_set.get(
                surface=alignment.grapheme)
        reduced_surface = _maybe_reduce(alignment, kanji_set)
        if reduced_surface == lexeme_surface.surface:
            partial_lexeme.surface_set.add(lexeme_surface)

        matching_reading = partial_lexeme.reading_set.get(
                reading=alignment.phoneme)
        partial_lexeme.reading_segments.get_or_create(
                syllabus=syllabus,
                lexeme_reading=matching_reading,
                segments=_format_alignment(alignment),
            )

    _log.finish('%d reduced surfaces' % n_reduced)
    return kanji_set

def _load_word_list(word_file, syllabus):
    _log.start('Parsing word list', nSteps=1)
    n_ok = 0
    skipped = []
    known_surfaces = {}
    for reading, surface, disambiguation in _SyllabusParser(word_file):
        lexeme = _find_matching_lexeme(reading, surface, skipped,
                disambiguation)
        surface_set = known_surfaces.setdefault(lexeme, set())
        surface_set.add(surface)
        if not lexeme:
            continue
        partial_lexeme = syllabus.partiallexeme_set.get_or_create(
                lexeme=lexeme)[0]
        partial_lexeme.reading_set.add(lexeme.reading_set.get(reading=reading))
        if disambiguation:
            partial_lexeme.sensenote_set.create(note=disambiguation)
        n_ok += 1
    _log.log('%d ok, %d skipped (see skipped.log)' % (n_ok, len(skipped)))

    o_stream = sopen('skipped.log', 'w')
    print >> o_stream, "# vim: set ts=20 noet sts=20:"
    for skipped_word in skipped:
        print >> o_stream, skipped_word
    o_stream.close()
    _log.finish()

#----------------------------------------------------------------------------#

def _maybe_reduce(alignment, kanji_set):
    """
    Remove any kanji from a surface which aren't in the kanji set, replacing
    replacing them with their kana reading.
    """
    result = []
    kanji_script = scripts.Script.Kanji
    for g_seg, p_seg in alignment:
        if scripts.scriptType(g_seg) == kanji_script and \
                g_seg in kanji_set:
            result.append(g_seg)
        else:
            result.append(p_seg)

    return u''.join(result)

#----------------------------------------------------------------------------#

class _SyllabusParser(object):
    """Parses files in the standard syllabus format."""
    def __init__(self, filename):
        self.filename = filename
        self.i_stream = sopen(filename)
        self.kanji = set()
    
    def __iter__(self):
        for line in self.i_stream:
            if line.startswith(u'#'):
                continue
            line = line.rstrip('\n')
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
        (reading, surface, disambiguation) = line.rstrip('\n').split('\t')
        return reading, surface, disambiguation
    
    def __del__(self):
        self.i_stream.close()
        
#----------------------------------------------------------------------------#

def _load_kanji_list(char_file, syllabus):
    _log.start('Loading kanji list', nSteps=1)

    i_stream = sopen(char_file)
    kanji_set = scripts.uniqueKanji(i_stream.read())
    for kanji in kanji_set:
        syllabus.partialkanji_set.create(
                kanji=lexicon_models.Kanji.objects.get(kanji=kanji))
    i_stream.close()

    _log.finish('%d kanji' % len(kanji_set))

#----------------------------------------------------------------------------#

def _load_kanji_readings(alignments, syllabus):
    _log.start('Loading kanji readings', nSteps=2)

    _log.log('Parsing alignments')
    readings = _get_kanji_alignment_readings(alignments)

    _match_readings(readings, syllabus)

    _log.finish()

def _match_readings(known_readings, syllabus):
    _log.start('Matching with known readings', nSteps=1)
    n_kanji = 0
    n_fallback = 0
    for partial_kanji in syllabus.partialkanji_set.all():
        n_kanji += 1
        kanji = partial_kanji.kanji.kanji
        real_readings = partial_kanji.kanji.reading_set

        # Try to save all the matched readings in bulk
        partial_kanji.reading_set = real_readings.filter(
                reading__in=known_readings.get(kanji, []))

        if partial_kanji.reading_set.count() == 0:
            # None-matched, fall back to the single most frequent reading
            # we can find.
            n_fallback += 1
            best_readings = lexicon_models.KanjiReadingCondProb.objects.filter(
                    condition=kanji).order_by('-pdf')
            for best_reading in best_readings:
                reading = best_reading.symbol
                try:
                    real_reading = real_readings.filter(reading=reading)[0]
                    break
                except IndexError:
                    pass
            else:
                raise Exception("none of our readings match")
            partial_kanji.reading_set.add(real_reading)

    _log.finish('%d kanji, %d/%d matched/fallback' % (
            n_kanji, n_kanji - n_fallback, n_fallback))

def _get_kanji_alignment_readings(alignments):
    kanji_script = scripts.Script.Kanji
    readings = {}
    for alignment in alignments:
        alignment_len = len(alignment)
        for i, (g_seg, p_seg) in enumerate(zip(alignment.g_segs,
                    alignment.p_segs)):
            if len(g_seg) > 1 or scripts.scriptType(g_seg) != kanji_script:
                continue
            reading_set = readings.setdefault(g_seg, set())
            reading_set.add(p_seg)

            has_left_context = i > 0
            has_right_context = i < alignment_len - 1
            extra_variants = alternations.canonicalSegmentForms(p_seg,
                    leftContext=has_left_context,
                    rightContext=has_right_context)
            reading_set.update(extra_variants)

    return readings

def _format_alignment(alignment):
    result = []
    for g_seg, p_seg in zip(alignment.g_segs, alignment.p_segs):
        if scripts.scriptType(g_seg) == scripts.Script.Kanji:
            result.append(p_seg)
        else:
            result.extend(p_seg)
    return '|'.join(result)

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

    parser.add_option('-f', '--force', action='store_true', dest='force',
            help='Overwrite any existing data.')

    parser.add_option('-u', '--user', action='store', dest='user',
            help='Manually initialise error distributions for a user.')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if options.list_syllabi:
        list_syllabi()

    elif options.user:
        add_per_user_models(options.user)

    elif options.all:
        add_all_syllabi(force=bool(options.force))

    elif len(args) == 1:
        syllabus_name = args[0]
        add_syllabus(syllabus_name, force=bool(options.force))

    else:
        parser.print_help()
        sys.exit(1)

    return

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
