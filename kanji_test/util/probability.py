# -*- coding: utf-8 -*-
# 
#  probability.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-30.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import math

from nltk import probability as nltk_prob
from cjktools.common import sopen

class FreqDist(nltk_prob.FreqDist):
    """
    >>> x = FreqDist()
    >>> x.inc('a', 5)
    >>> x['a']
    5
    """
    @staticmethod
    def from_file(filename):
        dist = FreqDist()
        i_stream = sopen(filename)
        for line in i_stream:
            symbol, count = line.rstrip().split()
            dist.inc(symbol, int(count))
        i_stream.close()
        return dist
    
    def to_file(self, filename):
        o_stream = sopen(filename, 'w')
        for sample in self.samples():
            count = self[sample]
            sample = unicode(sample)
            if len(sample.split()) > 1:
                raise ValueError('sample contains whitespace')
            print >> o_stream, u'%s %d' % (sample, count)
        o_stream.close()
        return

class ConditionalFreqDist(nltk_prob.ConditionalFreqDist):
    """
    >>> x = ConditionalFreqDist()
    >>> x['dog'].inc('barks')
    >>> x['dog'].freq('barks')
    1.0
    >>> x['cat'].inc('purrs', 1)
    >>> x['cat'].inc('scratches', 7)
    >>> x['cat'].samples()
    ['purrs', 'scratches']
    >>> x['cat'].freq('scratches')
    0.875
    """
    
    @classmethod
    def from_file(cls, filename, format='row'):
        if format == 'row':
            return cls.from_file_row_format(filename)
        elif format == 'packed':
            return cls.from_file_packed_format(filename)
        
        raise ValueError('invalid file format %s' % format)

    @staticmethod
    def from_file_row_format(filename):
        """
        Loads a distribution from a row_format file.
        """
        dist = ConditionalFreqDist()
        i_stream = sopen(filename)
        for line in i_stream:
            condition, symbol, count = line.rstrip().split()
            count = int(count)
            dist[condition].inc(symbol, count)
        i_stream.close()
        return dist
    
    @staticmethod
    def from_file_packed_format(filename):
        """
        Loads a distribution from a packed format file. Rows in this file
        look like:
        
        conditionA symA:1,symB:10
        """
        dist = ConditionalFreqDist()
        i_stream = sopen(filename)
        for line in i_stream:
            condition, symbol_counts = line.split()
            for symbol_count in symbol_counts.split(','):
                symbol, count_str = symbol_count.split(':')
                count = int(count_str)
                dist[condition].inc(symbol, count)
        i_stream.close()
        return dist
    
    def to_file(self, filename):
        """Stores the distribution to a file."""
        o_stream = sopen(filename, 'w')
        for condition in self.conditions():
            cond_dist = self[condition]
            for sample in cond_dist.samples():
                count = cond_dist[sample]
                print >> o_stream, u'%s %s %d' % (condition, sample, count)
        o_stream.close()
        return
    
    def without_condition(self):
        """
        Returns a new frequency distribution where the condition is
        ignored.
        """
        result = FreqDist()
        for condition in self.conditions():
            cond_dist = self[condition]
            for symbol in cond_dist.samples():
                result.inc(symbol, cond_dist[symbol])
        return result

class UnsupportedMethodError(Exception):
    pass

class FixedProbDist(nltk_prob.ProbDistI):
    """A fixed probability distribution, not based on a FreqDist object."""
    def __init__(self, samples):
        cdf = 0.0
        backing_dist = {}
        for sample, pdf in samples:
            backing_dist[sample] = pdf
            cdf += pdf
        
        if abs(cdf - 1.0) > 1e-8:
            raise ValueError("probability mass must sum to 1.0")

        self._prob_dist = backing_dist        
    
    def max(self):
        raise UnsupportedMethodError
    
    def prob(self, key):
        return self._prob_dist.get(key, 0.0)
    
    def logprob(self, key):
        return math.log(self.prob(key))
