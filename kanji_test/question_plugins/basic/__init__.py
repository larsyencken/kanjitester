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

from kanji_test.drills import models.api import models as api_models
from kanji_test.drills import models.api import factory
from kanji_test.lexicon import models as lexicon_models
from kanji_test import settings

#----------------------------------------------------------------------------#

class ReadingQuestionFactory(factory.MultipleChoiceFactoryI):
    "Distractor readings are randomly sampled."
    question_type = 'pr'
    supports_kanji = True
    supports_words = True
    
    def get_word_question(self, word):
        if not self.is_valid_word(word):
            raise ValueError(word)

        lexeme_surface = lexicon_models.LexemeSurface.objects.get(
                surface=word)
        real_readings = [r.reading for r in 
                lexeme_surface.lexeme.reading_set.all()]
        answer = random.choice(real_readings)
        distractor_values = list(itertools.islice(
                    self._random_reading_iter(len(word), real_readings), 
                    settings.N_DISTRACTORS,
                ))
        question = self.build_question(
                pivot=word,
                pivot_type='w',
                stimulus=word,
            )
        question.add_options(distractor_values, answer)
        return question
            
    def get_kanji_question(self, kanji):
        if not self.is_valid_kanji(kanji):
            raise ValueError(kanji)

        real_readings = [r.reading for r in \
                lexicon_models.KanjiReading.objects.filter(kanji=kanji)]
        distractor_values = list(itertools.islice(
                self._random_reading_iter(1, real_readings),
                settings.N_DISTRACTORS,
            ))
        answer = random.choice(list(real_readings))
        question = self.build_question(
                pivot=kanji,
                pivot_type='k',
                stimulus=kanji,
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

class SurfaceQuestionFactory(factory.MultipleChoiceFactoryI):
    """
    Distractors are sampled randomly from the surface distribution.
    """
    question_type = 'gp'
    supports_words = True
    supports_kanji = True
    
    def get_kanji_question(self, kanji):
        kanji_row = lexicon_models.Kanji.objects.get(kanji=kanji)
        distractor_set = set()
        while len(distractor_set) < settings.N_DISTRACTORS:
            random_kanji = lexicon_models.KanjiProb.sample().symbol
            if random_kanji != kanji:
                distractor_set.add(random_kanji)
        distractor_values = list(distractor_set)
        question = self.build_question(
                pivot=kanji,
                pivot_type='k',
                stimulus=kanji_row.gloss,
            )
        question.add_options(distractor_values, kanji)
        return question
        
    def get_word_question(self, word):
        lexeme = lexicon_models.LexemeSurface.objects.get(surface=word).lexeme
        language = lexicon_models.Language.get_default()
        gloss = ', '.join(r.gloss for r in \
                lexeme.sense_set.filter(language=language))
        distractor_chars = map(list, [word] * settings.N_DISTRACTORS)
        for j in xrange(len(word)):
            if scripts.scriptType(word[j]) != scripts.Script.Kanji:
                continue
            
            for i in xrange(settings.N_DISTRACTORS):
                distractor_chars[i][j] = lexicon_models.KanjiProb.sample(
                        ).symbol
        
        distractors = [''.join(distractor) for distractor in distractor_chars]
        question = self.build_question(
                pivot=word,
                pivot_type='w',
                stimulus=gloss
            )
        question.add_options(distractors, word)
        return question

#----------------------------------------------------------------------------#

class GlossQuestionFactory(factory.MultipleChoiceFactoryI):
    """Distractor glosses are sampled randomly."""
    supports_kanji = True
    supports_words = True
    question_type = 'pg'

    def get_kanji_question(self, kanji):
        kanji_row = lexicon_models.Kanji.objects.get(kanji=kanji)
        answer = kanji_row.gloss
        distractor_values = set()
        while len(distractor_values) < settings.N_DISTRACTORS:
            candidate = lexicon_models.KanjiProb.sample().kanji.gloss
            if candidate != answer:
                distractor_values.add(candidate)
        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=kanji,
                pivot_type='k',
                stimulus=kanji,
            )
        question.add_options(distractor_values, answer)
        return question
    
    def get_word_question(self, word):
        word_row = lexicon_models.LexemeSurface.objects.get(
                surface=word).lexeme
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
                pivot=word,
                pivot_type='w',
                stimulus=word,
            )
        question.add_options(distractor_values, answer)
        return question
