# -*- coding: utf-8 -*-
# 
#  probability.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-30.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import random

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

    def itercounts(self):
        "Returns an iterator over (condition, symbol, count) pairs."
        for condition in self.conditions():
            cond_dist = self[condition]
            for symbol in cond_dist.samples():
                yield condition, symbol, cond_dist[symbol]

class UnsupportedMethodError(Exception):
    pass

class AbstractMethod(Exception): pass

# XXX Doesn't match NLTK interface.
class ProbDistI(object):
    def __init__(self):
        raise AbstractMethod

    def sample(self, exclude_set=None):
        """
        Randomly samples a single object such that the object is not present
        in the excluded set.
        """
        raise AbstractMethod

    def sample_n(self, n, exclude_set=None):
        """
        Randomly samples n objects without replacement, such that none are
        included in the exclude_set.
        """
        raise AbstractMethod

class ProbDist(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._refresh_cdf()

    @classmethod
    def from_query_set(cls, query_set):
        dist = cls()
        for row in query_set.values('symbol', 'pdf'):
            dist[row['symbol']] = row['pdf']

        dist.normalise()
        return dist

    def copy(self):
        new_dist = ProbDist(self)
        new_dist._cdf = self._cdf[:]
        return new_dist

    def __eq__(self, rhs):
        return set(self.items()) == set(rhs.items())

    def normalise(self):
        total = sum(self.itervalues())
        for key in self:
            self[key] /= total
        self._refresh_cdf()

    def save_to(self, manager, **kwargs):
        manager.filter(**kwargs).delete()
        cdf = 0.0
        for symbol, pdf in self.iteritems():
            row_kwargs = {}
            row_kwargs.update(kwargs)
            cdf += pdf
            row_kwargs['cdf'] = cdf
            row_kwargs['pdf'] = pdf
            row_kwargs['symbol'] = symbol
            manager.create(**row_kwargs)

        return

    def sample(self):
        target_cdf = random.random()
        for cdf, symbol in self._cdf:
            if cdf >= target_cdf:
                return symbol
        raise RuntimeError("couldn't sample successfully")

    def sample_n(self, n, exclude_set=None):
        exclude_set = exclude_set or set()

        include_set = set(self.keys()).difference(exclude_set)
        if n > len(include_set):
            raise ValueError("don't have %d unique values" % n)

        elif n == len(include_set):
            result = list(include_set)
            random.shuffle(result)
            return result

        tmp_dist = self.copy()
        for symbol in tmp_dist.keys():
            if symbol not in include_set:
                del tmp_dist[symbol]
        tmp_dist.normalise()

        result = set()
        while len(result) < n:
            symbol = tmp_dist.sample()
            result.add(symbol)
            del tmp_dist[symbol]
            tmp_dist.normalise()

        result = list(result)
        random.shuffle(result)
        return result

    def _refresh_cdf(self):
        cdf_seq = []
        cdf = 0.0
        for symbol, pdf in self.iteritems():
            cdf += pdf
            cdf_seq.append((cdf, symbol))

        self._cdf = cdf_seq

# XXX Doesn't match NLTK interface.
class CondProbDist(dict):
    def __init__(self, *args, **kwargs):
        super(dict, self).__init__(*args, **kwargs)
    
    @classmethod
    def from_query_set(cls, query_set):
        dist = cls()
        for row in query_set.values('condition', 'symbol', 'pdf'):
            condition = row['condition']
            symbol = row['symbol']
            symbol_dist = dist.get(condition)
            if symbol_dist:
                symbol_dist[symbol] = row['pdf']
            else:
                dist[condition] = ProbDist({symbol: row['pdf']})
        return dist

    def normalise(self):
        for sub_dist in self.itervalues():
            sub_dist.normalise()

    def save_to(self, manager, **kwargs):
        manager.filter(**kwargs).delete()
        for condition, sub_dist in self.iteritems():
            sub_dist_kwargs = kwargs.copy()
            sub_dist_kwargs['condition'] = condition
            sub_dist.save_to(manager, **sub_dist_kwargs)

class SeqDist(ProbDist):
    """
    A distribution constructed as a sequence of smaller distributions.
    """
    def __init__(self, *dists):
        dict.__init__(self)
        old_dist = {(): 1.0}
        if not dists:
            raise ValueError("cannot be constructed empty")

        for new_dist in dists:
            if isinstance(new_dist, ProbDist):
                current = {} 
                for old_seq, old_pdf in old_dist.iteritems():
                    for new_symbol, new_pdf in new_dist.iteritems():
                        current[old_seq + (new_symbol,)] = old_pdf * new_pdf
                old_dist = current
            else:
                fixed_char = new_dist
                old_dist = dict((k + (fixed_char,), v) for (k,v) in \
                        old_dist.iteritems())

        self._segments = {}
        for segments, pdf in old_dist.iteritems():
            flat = u''.join(segments)
            # Overwrite alternative segmentations (simplification)
            self._segments[flat] = segments
            self[flat] = self.get(flat, 0.0) + pdf
        self.normalise()

    def sample(self):
        "Samples a segmented sequence from this distribution."
        return self._segments[ProbDist.sample(self)]

    def sample_n(self, n, exclude_set=None):
        "Samples n segmented sequences from this distribution."
        return map(
                self._segments.__getitem__,
                ProbDist.sample_n(self, n, exclude_set),
            )

