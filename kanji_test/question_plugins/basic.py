# -*- coding: utf-8 -*-
# 
#  __init__.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

import random
import itertools

from cjktools import scripts
from cjktools import sequences
from django.core.exceptions import ObjectDoesNotExist

from kanji_test.drills import models as api_models
from kanji_test.drills import plugin_api
from kanji_test.lexicon import models as lexicon_models
from kanji_test.user_model import models as usermodel_models
from kanji_test import settings

#----------------------------------------------------------------------------#

class ReadingQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    "Distractor readings are randomly sampled."
    question_type = 'pr'
    supports_kanji = True
    supports_words = True

    def get_word_question(self, partial_lexeme):
        try:
            surface = partial_lexeme.random_kanji_surface
        except ObjectDoesNotExist:
            raise plugin_api.UnsupportedItem(partial_lexeme)

        real_readings = [r.reading for r in 
                partial_lexeme.lexeme.reading_set.all()]
        answer = partial_lexeme.reading_set.all().order_by('?')[0].reading
        distractor_values = list(itertools.islice(
                    self._random_reading_iter(len(surface), real_readings), 
                    settings.N_DISTRACTORS,
                ))
        while len(distractor_values) > len(set(distractor_values)):
            distractor_values = list(itertools.islice(
                        self._random_reading_iter(len(surface), real_readings), 
                        settings.N_DISTRACTORS,
                    ))

        question = self.build_question(
                pivot=surface,
                pivot_type='w',
                stimulus=surface,
            )
        question.add_options(distractor_values, answer)
        return question
            
    def get_kanji_question(self, partial_kanji):
        real_readings = [r.reading for r in \
                partial_kanji.kanji.reading_set.all()]
        distractor_values = list(itertools.islice(
                self._random_reading_iter(1, real_readings),
                settings.N_DISTRACTORS,
            ))
        answer = random.choice(list(real_readings))
        question = self.build_question(
                pivot=partial_kanji.kanji.kanji,
                pivot_type='k',
                stimulus=partial_kanji.kanji.kanji,
            )
        question.save()
        question.add_options(distractor_values, answer)
        return question
    
    def _random_reading_iter(self, length, real_reading_set):
        """Returns a random iterator over kanji readings."""
        while True:
            reading_parts = []
            for i in xrange(length):
                reading_parts.append(
                        lexicon_models.KanjiReadingProb.sample().symbol
                    )
            reading = ''.join(reading_parts)
            if reading not in real_reading_set:
                yield reading

#----------------------------------------------------------------------------#

class SurfaceQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    """
    Distractors are sampled randomly from the surface distribution.
    """
    question_type = 'gp'
    supports_words = True
    supports_kanji = True
    
    def get_kanji_question(self, partial_kanji):
        kanji_row = partial_kanji.kanji
        kanji = kanji_row.kanji
        distractor_set = set()
        while len(distractor_set) < settings.N_DISTRACTORS:
            random_kanji = lexicon_models.KanjiProb.sample().symbol
            if random_kanji != kanji:
                distractor_set.add(random_kanji)
        distractor_values = list(distractor_set)
        question = self.build_question(
                pivot=partial_kanji.kanji.kanji,
                pivot_type='k',
                stimulus=kanji_row.gloss,
            )
        question.add_options(distractor_values, kanji)
        return question
        
    def get_word_question(self, partial_lexeme):
        lexeme = partial_lexeme.lexeme
        try:
            surface = partial_lexeme.random_kanji_surface
        except ObjectDoesNotExist:
            raise plugin_api.UnsupportedItem(partial_lexeme)

        language = lexicon_models.Language.get_default()
        # XXX assuming the first sense is the most frequent
        gloss = lexeme.sense_set.filter(language=language)[0].gloss
        distractor_chars = map(list, [surface] * settings.N_DISTRACTORS)
        for j in xrange(len(surface)):
            if scripts.scriptType(surface[j]) != scripts.Script.Kanji:
                continue
            
            for i in xrange(settings.N_DISTRACTORS):
                distractor_chars[i][j] = lexicon_models.KanjiProb.sample(
                        ).symbol
        
        distractors = [''.join(distractor) for distractor in distractor_chars]
        question = self.build_question(
                pivot=surface,
                pivot_type='w',
                stimulus=gloss
            )
        question.add_options(distractors, surface)
        return question

#----------------------------------------------------------------------------#

class GlossQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    """Distractor glosses are sampled randomly."""
    supports_kanji = True
    supports_words = True
    question_type = 'pg'

    def get_kanji_question(self, partial_kanji):
        kanji_row = partial_kanji.kanji
        answer = kanji_row.gloss
        distractor_values = set()
        while len(distractor_values) < settings.N_DISTRACTORS:
            candidate = lexicon_models.KanjiProb.sample().kanji.gloss
            if candidate != answer:
                distractor_values.add(candidate)
        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=kanji_row.kanji,
                pivot_type='k',
                stimulus=kanji_row.kanji,
            )
        question.add_options(distractor_values, answer)
        return question
    
    def get_word_question(self, partial_lexeme):
        try:
            surface = partial_lexeme.random_surface
        except ObjectDoesNotExist:
            raise plugin_api.UnsupportedItem(partial_lexeme)

        word_row = partial_lexeme.lexeme
        answer = word_row.random_sense.gloss
        distractor_values = set()
        while len(distractor_values) < settings.N_DISTRACTORS:
            # Find a random gloss by sampling a random surface and taking
            # its gloss. Only surfaces containing kanji are eligible.
            random_surface = lexicon_models.LexemeSurface.sample()
            if random_surface != answer and \
                    scripts.containsScript(scripts.Script.Kanji,
                            random_surface.surface):
                distractor_values.add(
                        random_surface.lexeme.random_sense.gloss
                    )
        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=surface,
                pivot_type='w',
                stimulus=surface,
            )
        question.add_options(distractor_values, answer)
        return question
