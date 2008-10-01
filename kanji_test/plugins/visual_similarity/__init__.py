# -*- coding: utf-8 -*-
# 
#  __init__.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

"""
Plugin for visual similarity.
"""

import random

from cjktools import scripts

from kanji_test import settings
from kanji_test.lexicon import models as lexicon_models
from kanji_test.plugins.api import factory
from kanji_test.plugins.visual_similarity import models

#----------------------------------------------------------------------------#

class SimilarityWithReading(factory.MultipleChoiceFactoryI):
    """
    Distractors are chosen via visual similarity.
    """
    supports_kanji = True
    supports_words = False
    question_type = 'rp'
    
    def get_kanji_question(self, kanji):
        if not self.is_valid_kanji(kanji):
            raise ValueError(kanji)
                
        # Sample a reading according to this kanji's reading distribution.
        reading = lexicon_models.KanjiReadingCondProb.sample(kanji).symbol
        answer = kanji
        
        # Get the distractor set.
        edge_set = list(models.SimilarityEdge.objects.filter(label=kanji
                ).order_by('weight'))
        
        # 4. Filter out distractors which have the given reading.
        filtered_options = []
        for edge in edge_set:
            if lexicon_models.KanjiReading.objects.filter(
                        kanji=edge.neighbour_label,
                        reading=reading
                    ).count() == 0:
                filtered_options.append(edge)
        
        # 5. Randomly choose amongst remaining distractors according to
        #    weight.
        # random.shuffle(filtered_options)
        distractor_values = [edge.neighbour_label for edge in filtered_options]
        distractor_values = distractor_values[:settings.N_DISTRACTORS]

        question = self.build_question(
                pivot=kanji,
                pivot_type='k',
                stimulus=reading,
            )
        question.add_options(distractor_values, answer)
        return question

#----------------------------------------------------------------------------#

class SimilarityWithMeaning(factory.MultipleChoiceFactoryI):
    """
    Distractors are chosen via visual similarity.
    """
    question_type = 'gp'
    supports_words = False
    supports_kanji = True
        
    def get_kanji_question(self, kanji):
        kanji_row = lexicon_models.Kanji.objects.get(kanji=kanji)
        neighbour_rows = models.SimilarityEdge.objects.filter(label=kanji
                ).order_by('weight')[:settings.N_DISTRACTORS]
        distractor_values = [row.neighbour_label for row in neighbour_rows]
        
        question = self.build_question(
                pivot=kanji,
                pivot_type='k',
                stimulus=kanji_row.gloss,
            )
        question.add_options(distractor_values, kanji)
        return question

#----------------------------------------------------------------------------#

def build():
    "Load the similarity graph into the database."
    import load_neighbours
    load_neighbours.load_neighbours()
