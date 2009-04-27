#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  add_syllabus.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-22.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import sys, optparse

from cjktools.common import sopen
from cjktools import scripts
from cjktools import alternations
import consoleLog
from django.contrib.auth import models as auth_models
from checksum.models import Checksum

from kanji_test.lexicon import models as lexicon_models
from kanji_test.user_model import models as usermodel_models
from kanji_test.user_model import plugin_api

import bundle

#----------------------------------------------------------------------------#

_log = consoleLog.default

#----------------------------------------------------------------------------#
# ACTIONS
#----------------------------------------------------------------------------#

def list_syllabi():
    syllabi = bundle.list_names()
    _log.start('Available syllabi', nSteps=len(syllabi))
    for syllabus_name in syllabi:
        _log.log(syllabus_name)
    _log.finish()

#----------------------------------------------------------------------------#

def add_all_syllabi(force=False):
    syllabi = bundle.list_names()
    _log.start('Adding all syllabi', nSteps=len(syllabi))

    dependencies = []
    for syllabus in syllabi:
        dependencies.extend(bundle.SyllabusBundle.get_dependencies(syllabus))

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

    _log.log('Loading bundle')
    syllabus_bundle = bundle.SyllabusBundle(syllabus_name)

    syllabus = _init_syllabus(syllabus_name)

    _store_kanji(syllabus, syllabus_bundle)
    _store_words(syllabus, syllabus_bundle)
    _store_kanji_readings(syllabus, syllabus_bundle)
    _store_word_surfaces(syllabus, syllabus_bundle)

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
    _log.log('Initialising syllabus object')
    tag = syllabus_name.replace('_', ' ')
    usermodel_models.Syllabus.objects.filter(tag=tag).delete()
    
    syllabus = usermodel_models.Syllabus(tag=tag)
    syllabus.save()
    return syllabus

def _find_in_lexicon(word, skipped_words, syllabus):
    """
    Attempts to find a unique match for this word in our lexicon. If we find
    one, we return it. Otherwise we record it as skipped, and return None.
    """
    matches = set(r.lexeme for r in \
            lexicon_models.LexemeReading.objects.filter(reading=word.reading))
    if word.surface:
        matches = matches.intersection(s.lexeme for s in \
                lexicon_models.LexemeSurface.objects.filter(
                        surface=word.surface))

    if len(matches) == 1:
        # A unique match!
        (lexeme,) = matches
        partial_lexeme = syllabus.partiallexeme_set.get_or_create(
                lexeme=lexeme)[0]
        partial_lexeme.reading_set.add(lexeme.reading_set.get(
                reading=word.reading))

        if word.notes:
            partial_lexeme.sensenote_set.create(note=word.notes)
        
        return partial_lexeme

    # We can't decide from here, so log an error.
    if len(matches) > 1:
        skipped_words.append((word, 'too many matches'))
    else:
        skipped_words.append((word, 'no match'))

    return
    
#----------------------------------------------------------------------------#

def _store_word_surfaces(syllabus, syllabus_bundle):
    """
    Aligns the word surfaces with JMdict. We also use our known kanji set,
    replacing any unknown kanji with their readings. If this results in a
    surface known to JMdict, then we add that surface to the lexeme's list.
    """
    _log.start('Building lexeme surfaces', nSteps=2)

    _store_reduced_surfaces(syllabus, syllabus_bundle)

    _log.log('Adding non-syllabus surfaces which match')
    for partial_lexeme in syllabus.partiallexeme_set.all():
        # Only add new surfaces if we had no matches
        if partial_lexeme.surface_set.count() > 0:
            continue

        for lexeme_surface in partial_lexeme.lexeme.surface_set.all():
            if scripts.unique_kanji(lexeme_surface.surface).issubset(
                    syllabus_bundle.chars):
                partial_lexeme.surface_set.add(lexeme_surface)

    _log.finish()

#----------------------------------------------------------------------------#

def _store_reduced_surfaces(syllabus, syllabus_bundle):
    """
    We may have some but not all of the kanji found in a surface available
    as part of the syllabus. In these cases, we see if variants of the surface
    which don't use the missing kanji are also available.
    """
    _log.start('Finding reduced surfaces', nSteps=1)
    n_aligned = 0
    for alignment in syllabus_bundle.alignments:
        if not alignment.has_kanji():
            continue

        # Find the word which this alignment represents.
        try:
            partial_lexeme = syllabus.partiallexeme_set.filter(
                    lexeme__reading_set__reading=alignment.phoneme).get(
                    lexeme__surface_set__surface=alignment.grapheme)
        except:
            continue

        reading = partial_lexeme.reading_set.get(reading=alignment.phoneme)
        surface = partial_lexeme.lexeme.surface_set.get(
            surface=alignment.grapheme)

        if scripts.unique_kanji(surface.surface).issubset(
                    syllabus_bundle.chars):
            partial_lexeme.surface_set.add(surface)
            syllabus.alignment_set.get_or_create(
                    reading=reading,
                    surface=surface,
                    alignment=alignment.short_form(),
                )
            n_aligned += 1

    _log.finish('%d reduced surfaces' % n_aligned)
    return

def _store_words(syllabus, syllabus_bundle):
    """
    Try to find a matching lexicon word for each word in the syllabus, then
    store the limited knowledge we have about it in a partial lexeme object.
    """
    _log.start('Parsing word list', nSteps=1)
    n_ok = 0
    skipped_words = []
    for word in syllabus_bundle.words: 
        partial_lexeme = _find_in_lexicon(word, skipped_words, syllabus)
        if partial_lexeme:
            n_ok += 1
    _log.log('%d ok, %d skipped (see skipped.log)' % (n_ok,
            len(skipped_words)))

    o_stream = sopen('skipped.log', 'w')
    vim_header = "# vim: set ts=20 noet sts=20:"
    print >> o_stream, vim_header
    for word, reason in skipped_words:
        print >> o_stream, '%s\t%s' % (word.to_line(), reason)
    o_stream.close()
    _log.finish()

#----------------------------------------------------------------------------#

def _store_kanji(syllabus, syllabus_bundle):
    _log.log('Storing %d kanji' % len(syllabus_bundle.chars))
    for kanji in syllabus_bundle.chars:
        syllabus.partialkanji_set.create(
                kanji=lexicon_models.Kanji.objects.get(kanji=kanji))

#----------------------------------------------------------------------------#

def _store_kanji_readings(syllabus, bundle):
    "Store the limited knowledge of kanji readings required by this syllabus."
    _log.log('Loading kanji readings')
    reading_map = _get_kanji_readings(bundle.alignments)
    _prune_readings(reading_map, syllabus)

def _prune_readings(known_readings, syllabus):
    """
    Given a map of kanji readings, we prune the map back to only those which
    are valid readings from our lexicon, and store those.
    """
    _log.start('Matching with known readings', nSteps=1)
    n_kanji = 0
    n_fallback = 0
    for partial_kanji in syllabus.partialkanji_set.all():
        n_kanji += 1
        kanji = partial_kanji.kanji.kanji
        valid_readings = partial_kanji.kanji.reading_set

        # Try to save all the matched readings in bulk
        partial_kanji.reading_set = valid_readings.filter(
                reading__in=known_readings.get(kanji, []))
        if partial_kanji.reading_set.count() > 0:
            continue

        # None-matched, just add the single most frequent reading we can find.
        n_fallback += 1
        frequent_readings = lexicon_models.KanjiReadingCondProb.objects.filter(
                condition=kanji).order_by('-pdf')
        for reading in frequent_readings:
            filtered_readings = valid_readings.filter(reading=reading.symbol)
            if filtered_readings.count() > 0:
                partial_kanji.reading_set.add(filtered_readings[0])
                break
        else:
            raise Exception("none of our readings match")

    _log.finish('%d kanji, %d/%d matched/fallback' % (
            n_kanji, n_kanji - n_fallback, n_fallback))

def _get_kanji_readings(alignments):
    """
    Develop a set of readings for each kanji which a learner must know as part
    of this syllabus. This set may contain invalid readings, and will later
    be pruned to only valid readings.
    """
    kanji_script = scripts.Script.Kanji
    readings = {}
    for alignment in alignments:
        alignment_len = len(alignment)
        for i, (g_seg, p_seg) in enumerate(zip(alignment.g_segs,
                    alignment.p_segs)):
            if len(g_seg) > 1 or scripts.script_types(g_seg) != kanji_script:
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
        if scripts.script_types(g_seg) == scripts.Script.Kanji:
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
