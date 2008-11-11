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

from kanji_test.user_model import plugin_api
from kanji_test.lexicon import models
from kanji_test import settings

import metrics
import threshold_graph

_default_metric_name = 'stroke edit distance'
_log = consoleLog.default

class VisualSimilarity(plugin_api.UserModelPlugin):
    def __init__(self):
        self.dist_name = "kanji' | kanji"

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
            models.Kanji.objects.filter(partialkanji__syllabus=syllabus)])

        _log.log('Generating similarity graph ', newLine=False)
        graph = self._build_graph(kanji_set)

        _log.log('Storing priors')
        self._store_graph(graph, prior_dist)

        _log.finish()

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
                kanji = _getMessage(e)
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
                        is_correct=(label == neighbour_label),
                    )

