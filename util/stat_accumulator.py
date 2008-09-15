# -*- coding: utf-8 -*-
# 
#  stat_accumulator.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-15.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import math

class StatAccumulator(object):
    """
    A basic system for maintaining statistics about a sequence.
    
    >>> x = StatAccumulator()
    >>> for i in range(3): x.inc(i)
    >>> x.mean
    1.0
    >>> abs(x.stddev - 0.8164966) < 1e-4
    True
    
    >>> y = StatAccumulator()
    >>> for i in range(1001): y.inc(i)
    >>> y.mean
    500.0
    >>> abs(y.stddev - 288.9637) < 1e-4
    True
    """
    def __init__(self):
        self._n = 0
        self._sum = 0.0
        self._sum_squared = 0.0
    
    def inc(self, value):
        "Includes a value in the statistics being gathered."
        self._n += 1
        self._sum += value
        self._sum_squared += value*value;
    
    def inc_all(self, seq):
        "Increments the statistics for all values in the sequence."
        for value in seq:
            self.inc(value)
    
    def iter_inc(self, seq):
        """
        Returns an interator over the sequence which increments as a 
        side-effect.
        """
        for value in seq:
            self.inc(value)
            yield value
        
    def mean():
        doc = "The mean of the sequence."
        def fget(self):
            return self._sum / self._n
        return locals()
    mean = property(**mean())
    
    def var():
        doc = "The variance of the sequence."
        def fget(self):
            return self._sum_squared / self._n - (self.mean ** 2)
        return locals()
    var = property(**var())
    
    def stddev():
        doc = "The standard deviation of the sequence."
        def fget(self):
            return math.sqrt(self.var)
        return locals()
    stddev = property(**stddev())
