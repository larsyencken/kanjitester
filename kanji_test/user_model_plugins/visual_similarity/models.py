# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-12.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import os

from django.db import models

class Edge(models.Model):
    "A weighted edge for an undirected graph."
    label = models.CharField(max_length=100, db_index=True)
    neighbour_label = models.CharField(max_length=100)
    weight = models.FloatField()
    
    class Meta:
        abstract = True
        verbose_name_plural = 'graph'
        unique_together = (('label', 'neighbour_label'),)

    def __unicode__(self):
        return u"%s <-> %s (%g)" % (self.label, self.neighbour_label,
                self.weight)

class SimilarityEdge(Edge):
    class Meta(Edge.Meta):
        verbose_name_plural = 'similarity graph'
    
    def __unicode__(self):
        return u"%s <-> %s (%g)" % (self.label, self.neighbour_label,
                self.weight)
