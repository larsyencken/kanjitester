# -*- coding: utf-8 -*-
# 
#  prob_models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-17.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

"""
Abstract models for probability distributions.
"""

import random

from django.db import models

class ProbI(models.Model):
    """A probabilty distribution."""
    pdf = models.FloatField()
    cdf = models.FloatField()
        
    class Meta:
        abstract = True

    @classmethod
    def sample(cls):
        """Samples and returns an object from this distribution."""
        target_cdf = random.random()
        result = cls.objects.filter(cdf__gte=target_cdf).order_by('cdf')[0]
        return result

class Prob(ProbI):
    """A basic probability distribution."""
    symbol = models.CharField(max_length=50, db_index=True, unique=True)
        
    class Meta:
        abstract = True
        ordering = ['-pdf', 'symbol']
    
    @classmethod
    def from_dist(cls, prob_dist):
        cls.objects.all().delete()
        cdf = 0.0
        for symbol in prob_dist.samples():
            pdf = prob_dist.freq(symbol)
            cdf += pdf
            row = cls(symbol=symbol, pdf=pdf, cdf=cdf)
            row.save()
        return

class CondProb(ProbI):
    """A conditional probability distribution."""
    condition = models.CharField(max_length=50, db_index=True)
    symbol = models.CharField(max_length=50, db_index=True)

    class Meta:
        abstract = True
        unique_together = (('condition', 'symbol'),)
        ordering = ['condition', '-pdf', 'symbol']

    @classmethod
    def sample(cls, condition):
        """
        Samples and returns an object from this distribution given the 
        condition.
        """
        target_cdf = random.random()
        result = cls.objects.filter(condition=condition, cdf__gte=target_cdf
                ).order_by('cdf')[0]
        return result

    @classmethod
    def from_dist(cls, cond_prob_dist):
        cls.objects.all().delete()
        for condition in cond_prob_dist.conditions():
            cdf = 0.0
            prob_dist = cond_prob_dist[condition]
            for symbol in prob_dist.samples():
                pdf = prob_dist.freq(symbol)
                cdf += pdf
                row = cls(condition=condition, symbol=symbol, pdf=pdf,
                        cdf=cdf)
                row.save()
        return                


