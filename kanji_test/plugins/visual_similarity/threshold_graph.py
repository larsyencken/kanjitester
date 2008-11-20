# -*- coding: utf-8 -*-
# 
#  threshold_graph.py
#  label_test
#  
#  Created by Lars Yencken on 2008-09-15.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

"""
An auto-pruning weighted graph which only keeps the n highest weight links
from each node to each other.
"""

import math
import heapq

from django.db import connection

class ThresholdLinkset(object):
    """
    A list of links to a vertex with limited degree. Beyond that threshold,
    only the lowest weight links are kept.
    """
    __slots__ = '_max_degree', '_heap'
    def __init__(self, max_degree):
        self._max_degree = max_degree
        self._heap = []

    def add(self, label, weight):
        heapq.heappush(self._heap, (-weight, label))
        if len(self._heap) > self._max_degree:
            heapq.heappop(self._heap)

    def get_links(self):
        return self._heap
    
    def __iter__(self):
        for neg_weight, label in self._heap:
            yield -neg_weight, label

class ThresholdGraph(object):
    """
    A weighted graph where the maximum degree of each node is set. Beyond that,
    only the links with the lowest weight are kept. The base graph is
    undirected, but after pruning the graph is directed.
    """
    def __init__(self, max_degree):
        self._max_degree = max_degree
        self._heaps = {}
        self._sum = 0.0
        self._n_links = 0
        self._sum_squared = 0.0

    def connect(self, label_a, label_b, weight):
        self[label_a].add(label_b, weight)
        if label_a != label_b:
            self[label_b].add(label_a, weight)
        self._n_links += 1
        self._sum += weight
        self._sum_squared += weight * weight

    def __getitem__(self, label):
        heap = self._heaps.get(label)
        return heap or self._heaps.setdefault(
                label,
                ThresholdLinkset(self._max_degree)
            )
    
    def labels(self):
        return self.heaps.labels()
