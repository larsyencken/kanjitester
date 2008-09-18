#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  load_neighbours.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-15.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import os, sys, optparse

from cjktools.common import sopen
from cjktools.scripts import uniqueKanji
from cjktools.shell import setScreenTitle
from cjktools.stats import iuniquePairs 
from cjktools.exceptions import DomainError
from cjktools.resources import kanjiList
import consoleLog

from plugins.visual_similarity import models, threshold_graph, metrics
import settings

#----------------------------------------------------------------------------#
# PUBLIC
#----------------------------------------------------------------------------#

log = consoleLog.default

_default_list_name = 'jp_jooyoo'
_default_metric_name = 'stroke edit distance'

#----------------------------------------------------------------------------#

def load_neighbours(list_name=_default_list_name,
            metric_name=_default_metric_name):
    "Populates the database with a neighbour graph."

    log.start('Loading neighbours into the database')
    kanji_set = kanjiList.getList(list_name)
    metric = metrics.metric_library[metric_name]
    
    log.log('Calculating similarity ', newLine=False)
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

    log.log('Storing to the database')
    graph.store(models.SimilarityEdge)
    log.finish()
    return

#----------------------------------------------------------------------------#
# PRIVATE
#----------------------------------------------------------------------------#

def _getMessage(e):
    "Returns the original exception message given the exception itself."
    while type(e) not in [str, unicode]:
        e = e.message

    return e

#----------------------------------------------------------------------------#
# MODULE EPILOGUE
#----------------------------------------------------------------------------#

def _createOptionParser():
    usage = \
"""%%prog [-l list_name] [-m metric_name]

Builds a similarity graph using the similarity metric given. For the graph
to have some salience, it is pruned to only the top %d edges for each 
vertex.""" % settings.MAX_GRAPH_DEGREE

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            default=False, help='Enables debugging mode [False]')
    
    parser.add_option('-l', '--list', action='store', dest='list_name',
            default=_default_list_name,
            help='The kanji list to use [jp_jooyoo]')
    
    parser.add_option('-m', '--metric', action='store', dest='metric_name',
            default=_default_metric_name,
            help='The similarity metric to use [stroke edit distance]')
    
    return parser

#----------------------------------------------------------------------------#

def main(argv):
    parser = _createOptionParser()
    (options, args) = parser.parse_args(argv)

    if args:
        parser.print_help()
        sys.exit(1)

    if not options.debug:
        try:
            import psyco
            psyco.profile()
        except:
            pass

    load_neighbours(options.list_name, options.metric_name)
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

#----------------------------------------------------------------------------#
  
# vim: ts=4 sw=4 sts=4 et tw=78:
