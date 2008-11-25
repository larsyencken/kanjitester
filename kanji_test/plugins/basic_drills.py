# -*- coding: utf-8 -*-
# 
#  basic_drills.py
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

from kanji_test.drill import models as api_models
from kanji_test.drill import plugin_api, support
from kanji_test.lexicon import models as lexicon_models
from kanji_test.user_model import models as usermodel_models
from kanji_test import settings

#----------------------------------------------------------------------------#

class ReadingQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    "Distractor readings are randomly sampled."
    question_type = 'pr'
    requires_kanji = True
    supports_kanji = True
    supports_words = True
    uses_dist = None

    def get_word_question(self, partial_lexeme, _user):
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
                pivot_id=partial_lexeme.id,
                pivot_type='w',
                stimulus=surface,
            )
        question.add_options(distractor_values, answer)
        return question
            
    def get_kanji_question(self, partial_kanji, _user):
        real_readings = [r.reading for r in \
                partial_kanji.kanji.reading_set.all()]
        distractor_values = list(itertools.islice(
                self._random_reading_iter(1, real_readings),
                settings.N_DISTRACTORS,
            ))
        answer = partial_kanji.reading_set.order_by('?')[0].reading
        question = self.build_question(
                pivot=partial_kanji.kanji.kanji,
                pivot_id=partial_kanji.id,
                pivot_type='k',
                stimulus=partial_kanji.kanji.kanji,
            )
        question.save()
        question.add_options(distractor_values, answer)
        return question
    
    def _random_reading_iter(self, length, real_reading_set):
        """Returns a random iterator over kanji readings."""
        previous_set = set(real_reading_set)
        while True:
            reading_parts = []
            for i in xrange(length):
                reading_parts.append(
                        lexicon_models.KanjiReadingProb.sample().symbol
                    )
            reading = ''.join(reading_parts)
            if reading not in previous_set:
                yield reading
                previous_set.add(reading)

#----------------------------------------------------------------------------#

class SurfaceQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    "Distractors sampled randomly from a naive surface distribution."
    question_type = 'gp'
    requires_kanji = True
    supports_words = True
    supports_kanji = True
    uses_dist = None

    def get_kanji_question(self, partial_kanji, user):
        kanji_row = partial_kanji.kanji
        kanji = kanji_row.kanji
        distractors, _annotations = support.build_options(kanji,
                self._build_sampler(user))
        question = self.build_question(
                pivot=kanji,
                pivot_id=partial_kanji.id,
                pivot_type='k',
                stimulus=kanji_row.gloss,
            )
        question.add_options(distractors, kanji)
        return question
        
    def get_word_question(self, partial_lexeme, user):
        lexeme = partial_lexeme.lexeme
        try:
            surface = partial_lexeme.random_kanji_surface
        except ObjectDoesNotExist:
            raise plugin_api.UnsupportedItem(partial_lexeme)

        # Assume the first sense is the most frequent
        gloss = lexeme.sense_set.get(is_first_sense=True).gloss
        distractors, _annotations = support.build_options(surface,
                self._build_sampler(user))
        question = self.build_question(
                pivot=surface,
                pivot_id=partial_lexeme.id,
                pivot_type='w',
                stimulus=gloss
            )
        question.add_options(distractors, surface)
        return question

    def _build_sampler(self, user):
        if not hasattr(self, '_kanji_set'):
            self._kanji_set = [row.kanji for row in \
                    lexicon_models.Kanji.objects.filter(
                        partialkanji__syllabus__userprofile__user=user)
                ]

        def sample_n(char, n, exclude_set):
            if scripts.scriptType(char) == scripts.Script.Kanji:
                result = []
                available_set = list(set(self._kanji_set).difference(
                        exclude_set))
                if len(available_set) < n:
                    raise ValueError("don't have %d items to sample" % n)
                while len(result) < n:
                    kanji = random.choice(available_set)
                    result.append(kanji)
                    available_set.pop(available_set.index(kanji))
                return result
            else:
                return [char] * n

        return sample_n
    
#----------------------------------------------------------------------------#

class GlossQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    """Distractor glosses are sampled randomly."""
    supports_kanji = True
    supports_words = True
    requires_kanji = False
    question_type = 'pg'
    uses_dist = None

    def get_kanji_question(self, partial_kanji, user):
        kanji_row = partial_kanji.kanji
        answer = kanji_row.gloss
        syllabus = user.get_profile().syllabus
        distractor_values = set()
        while len(distractor_values) < settings.N_DISTRACTORS:
            for kanji in lexicon_models.Kanji.objects.filter(
                        partialkanji__syllabus=syllabus
                    ).order_by('?')[:settings.N_DISTRACTORS]:
                distractor = kanji.gloss
                if distractor != answer:
                    distractor_values.add(distractor)
                    if len(distractor_values) > settings.N_DISTRACTORS:
                        break

        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=kanji_row.kanji,
                pivot_id=partial_kanji.id,
                pivot_type='k',
                stimulus=kanji_row.kanji,
            )
        question.add_options(distractor_values, answer)
        return question
    
    def get_word_question(self, partial_lexeme, user):
        try:
            surface = partial_lexeme.random_surface
        except ObjectDoesNotExist:
            surface = partial_lexeme.random_reading

        word_row = partial_lexeme.lexeme
        
        answer = word_row.first_sense.gloss
        syllabus = user.get_profile().syllabus

        distractor_values = set()
        exclude_set = set(s.gloss for s in word_row.sense_set.all())
        while len(distractor_values) < settings.N_DISTRACTORS:
            for sense in syllabus.sample_senses(settings.N_DISTRACTORS):
                gloss = sense.gloss
                if gloss not in exclude_set:
                    distractor_values.add(gloss)
                    if len(distractor_values) == settings.N_DISTRACTORS:
                        break

        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=surface,
                pivot_id=partial_lexeme.id,
                pivot_type='w',
                stimulus=surface,
            )
        question.add_options(distractor_values, answer)
        return question

