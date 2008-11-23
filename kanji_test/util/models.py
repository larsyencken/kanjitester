# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-28.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

"""
Abstract models for probability distributions.
"""

import random
import operator

from django.db import models, connection
from cjktools.sequences import groupsOfN

from kanji_test.settings import N_ROWS_PER_INSERT

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

    @classmethod
    def sample_n(cls, n):
        if n < 1:
            raise ValueError(n)

        target_cdfs = [random.random() for i in xrange(n)]
        quote_name = connection.ops.quote_name
        table_name = quote_name(cls._meta.db_table)
        id_field = '%s.%s' % (table_name, quote_name('id'))
        cdf_field = '%s.%s' % (table_name, quote_name('cdf'))

        sql = ' OR '.join(
                ['%s = (select %s from %s where %s >= %f limit 1)' % (
                        id_field, id_field, table_name, cdf_field, cdf
                    ) for cdf in target_cdfs]
            )
        return cls.objects.extra(where=[sql])

class Prob(ProbI):
    """A basic probability distribution."""
    symbol = models.CharField(max_length=50, db_index=True, unique=True)
        
    class Meta:
        abstract = True
        ordering = ['-pdf', 'symbol']

    def __unicode__(self):
        return self.symbol

    @classmethod
    def from_dist(cls, prob_dist):
        table_name = cls._meta.db_table
        cursor = connection.cursor()
        cursor.execute('DELETE FROM %s' % table_name)

        rows = []
        cdf = 0.0
        for symbol in prob_dist.samples():
            pdf = prob_dist.freq(symbol)
            cdf += pdf
            rows.append((symbol, pdf, cdf))

        for row_set in groupsOfN(N_ROWS_PER_INSERT, rows):
            cursor.executemany(
                    """
                    INSERT INTO `%s` (`symbol`, `pdf`, `cdf`)
                    VALUES (%%s, %%s, %%s)
                    """ % table_name,
                    row_set
                )
        cursor.close()

class CondProb(ProbI):
    """A conditional probability distribution."""
    condition = models.CharField(max_length=50, db_index=True)
    symbol = models.CharField(max_length=50, db_index=True)

    class Meta:
        abstract = True
        unique_together = (('condition', 'symbol'),)
        ordering = ['condition', '-pdf', 'symbol']

    def __unicode__(self):
        return '%s | %s' % (self.symbol, self.condition)

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
        table_name = cls._meta.db_table
        cursor = connection.cursor()
        cursor.execute('DELETE FROM %s' % table_name)

        rows = []
        for condition in cond_prob_dist.conditions():
            cdf = 0.0
            prob_dist = cond_prob_dist[condition]
            for symbol in prob_dist.samples():
                pdf = prob_dist.freq(symbol)
                cdf += pdf
                rows.append((condition, symbol, pdf, cdf))

        for row_set in groupsOfN(N_ROWS_PER_INSERT, rows):
            cursor.executemany(
                    """
                    INSERT INTO `%s` (`condition`, `symbol`, `pdf`, `cdf`)
                    VALUES (%%s, %%s, %%s, %%s)
                    """ % table_name,
                    row_set
                )
        cursor.close()
