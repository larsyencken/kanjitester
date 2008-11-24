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

import consoleLog
from cjktools.stats import iuniquePairs
from cjktools.exceptions import DomainError
from cjktools import scripts
from django.core.exceptions import ObjectDoesNotExist

from kanji_test.user_model import plugin_api as user_model_api
from kanji_test.user_model import models as usermodel_models
from kanji_test.drill import plugin_api as drill_api
from kanji_test.drill import support
from kanji_test.lexicon import models as lexicon_models
from kanji_test import settings

import metrics
import threshold_graph

_default_metric_name = 'stroke edit distance'
_log = consoleLog.default

class VisualSimilarity(user_model_api.UserModelPlugin):
    dist_name = "kanji' | kanji"

    def init_priors(self, syllabus, force=False):
        prior_dist, created = syllabus.priordist_set.get_or_create(
                tag=self.dist_name)
        if not created:
            if not force:
                # Keep the existing distribution.
                return

            prior_dist.priorpdf_set.all().delete()

        _log.start("Building %s dist" % self.dist_name, nSteps=3)

        _log.log('Fetching syllabus kanji')
        kanji_set = set([k_row.kanji for k_row in
            lexicon_models.Kanji.objects.filter(
            partialkanji__syllabus=syllabus)])

        _log.log('Generating similarity graph ', newLine=False)
        graph = self._build_graph(kanji_set)

        _log.log('Storing priors')
        self._store_graph(graph, prior_dist)

        _log.finish()

    def update(self, response):
        "Update our error model from a user's response."
        error_dist = usermodel_models.ErrorDist.objects.get(user=response.user,
                tag=self.dist_name)
        question = response.question

        if question.pivot_type == 'k':
            self._update_kanji(response, error_dist)

        elif question.pivot_type == 'w':
            self._update_seq(response, error_dist)

        else:
            raise ValueError("unknown question type")

    def _update_kanji(self, response, error_dist):
        question = response.question
        sub_dist = usermodel_models.ProbDist(error_dist.density.filter(
                condition=question.pivot))
        option_values = [o['value'] for o in \
                question.multiplechoicequestion.options.all().values('value')]
        response_value = response.option.value
        distractors = [v for v in option_values if v != response_value]
        m = max(map(sub_dist.__getitem__, distractors)) + \
                settings.UPDATE_EPSILON
        if m > sub_dist[response_value]:
            sub_dist[response_value] = m
            sub_dist.normalise()
            sub_dist.save_to(error_dist.density, condition=question.pivot)
        return

    def _update_seq(self, response, error_dist):
        question = response.question
        option_values = [o['value'] for o in \
                question.multiplechoicequestion.options.all().values('value')]
        response_value = response.option.value
        distractors = [v for v in option_values if v != response_value]
        for i, char in enumerate(question.pivot):
            if scripts.scriptType(char) != scripts.Script.Kanji:
                continue

            sub_dist = usermodel_models.ProbDist(error_dist.density.filter(
                    condition=char))
            m = max(map(sub_dist.__getitem__, [v[i] for v in distractors])) + \
                    settings.UPDATE_EPSILON
            if m > sub_dist[response_value[i]]:
                sub_dist[response_value[i]] = m
                sub_dist.normalise()
                sub_dist.save_to(error_dist.density, condition=char)
        return

    def _build_graph(self, kanji_set):
        metric = metrics.metric_library[_default_metric_name]
        graph = threshold_graph.ThresholdGraph(settings.MAX_GRAPH_DEGREE)
        ignore_set = set()
        for kanji_a, kanji_b in consoleLog.withProgress(
                    iuniquePairs(kanji_set), 100):
            if kanji_a in ignore_set or kanji_b in ignore_set:
                continue

            try:
                weight = metric(kanji_a, kanji_b)
            except DomainError, e:
                kanji = e.message
                ignore_set.add(kanji)
                continue

            graph.connect(kanji_a, kanji_b, weight)

        for kanji in kanji_set:
            graph.connect(kanji, kanji, 0.0)

        return graph

    def _store_graph(self, graph, prior_dist):
        for label, edge_seq in graph._heaps.iteritems():
            total_weight = 0.0
            for weight, neighbour_label in edge_seq:
                total_weight += 1.0 - weight

            cdf = 0.0
            for weight, neighbour_label in edge_seq:
                pdf = (1.0 - weight) / total_weight
                cdf += pdf
                prior_dist.density.create(
                        condition=label,
                        symbol=neighbour_label,
                        pdf=pdf,
                        cdf=cdf,
                    )

#----------------------------------------------------------------------------#

class VisualSimilarityDrills(drill_api.MultipleChoiceFactoryI):
    "Distractors are sampled from the user error distribution."
    question_type = 'gp'
    supports_words = True
    supports_kanji = True
    requires_kanji = True
    uses_dist = "kanji' | kanji"

    def get_kanji_question(self, partial_kanji, user):
        self.error_dist = usermodel_models.ErrorDist.objects.get(user=user,
                tag=self.uses_dist)

        kanji_row = partial_kanji.kanji
        kanji = kanji_row.kanji
        question = self.build_question(
                pivot=kanji,
                pivot_type='k',
                stimulus=kanji_row.gloss,
            )
        self._add_distractors(question)
        return question
        
    def get_word_question(self, partial_lexeme, user):
        self.error_dist = usermodel_models.ErrorDist.objects.get(user=user,
                tag=self.uses_dist)
        lexeme = partial_lexeme.lexeme
        try:
            surface = partial_lexeme.random_kanji_surface
        except ObjectDoesNotExist:
            raise drill_api.UnsupportedItem(partial_lexeme)

        # Assume the first sense is the dominant sense
        gloss = lexeme.sense_set.get(is_first_sense=True).gloss

        question = self.build_question(
                pivot=surface,
                pivot_type='w',
                stimulus=gloss
            )
        self._add_distractors(question)
        return question

    def _add_distractors(self, question):
        """
        Builds distractors for the question with appropriate annotations so
        that we can easily update the error model afterwards.   
        """
        distractors, annotations = support.build_options(
                question.pivot, self._sample_kanji)
        question.add_options(distractors, question.pivot,
                annotations=annotations)
        question.annotation = u'|'.join(question.pivot)
        question.save()
        return

    def _sample_kanji(self, char):
        if scripts.scriptType(char) == scripts.Script.Kanji:
            return self.error_dist.sample(char).symbol

        return char

def segment_word(surface):
    """
    Finds the script boundaries of a word, but also creates a slot for each
    kanji in the word.

    >>> segment_word(unicode('感謝する', 'utf8'))
    (u'\u611f', u'\u8b1d', u'\u3059\u308b')
    """
    base_segments = scripts.scriptBoundaries(surface)
    kanji_script = scripts.Script.Kanji
    result = []
    for segment in base_segments:
        if scripts.scriptType(segment) == kanji_script:
            result.extend(segment)
        else:
            result.append(segment)

    return tuple(result)

