# -*- coding: utf-8 -*-
# 
#  __init__.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

"""
Basic question types which use the user's error distribution to select
distractors.
"""

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

class KanjiSimilarityDrills(plugin_api.MultipleChoiceFactoryI):
    "Distractors are sampled from the user error distribution."
    question_type = 'gp'
    supports_words = True
    supports_kanji = True
    requires_kanji = True
    uses_dist = "kanji' | kanji"
    
    def get_kanji_question(self, partial_kanji, user):
        kanji_row = partial_kanji.kanji
        error_dist = usermodel_models.ErrorDist.objects.get(user=user,
                tag=self.uses_dist)
        kanji = kanji_row.kanji
        sample_kanji = lambda char: error_dist.sample(char).symbol
        distractors = support.build_kanji_options(kanji, sample_kanji)
        question = self.build_question(
                pivot=kanji,
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

        error_dist = usermodel_models.ErrorDist.objects.get(user=user,
                tag=self.uses_dist)
        language = lexicon_models.Language.get_default()
        # XXX assuming the first sense is the most frequent
        gloss = lexeme.sense_set.filter(language=language)[0].gloss

        sample_kanji = lambda char: error_dist.sample(char).symbol
        distractors = support.build_kanji_options(surface, sample_kanji)
        question = self.build_question(
                pivot=surface,
                pivot_type='w',
                stimulus=gloss
            )
        question.add_options(distractors, surface)
        return question

