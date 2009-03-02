# -*- coding: utf-8 -*-
#
#  charts.py
#  kanji_test
# 
#  Created by Lars Yencken on 27-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

"""
Helper classes for working with Google Charts.
"""

import csv

from django.utils.http import urlencode
from cjktools.sequences import unzip

_google_charts_url = "http://chart.apis.google.com/chart?"
_default_size = '750x375'

class Chart(dict):
    """
    >>> Chart().get_url()
    'http://chart.apis.google.com/chart?chs=750x375'
    """

    def __init__(self, data, size=_default_size):
        dict.__init__(self)
        self.data = data
        self['chs'] = size
        self['chco'] = '3030ff' # blue colour, interpolated

    def set_size(self, size_spec):
        self['chs'] = size_spec

    def get_url(self):
        return _google_charts_url + dummy_urlencode(self)

    def get_data(self):
        return self.data

def dummy_urlencode(val_dict):
    parts = []
    for key, value in sorted(val_dict.items()):
        parts.append('%s=%s' % (key, value))
    return '&'.join(parts)

class PieChart(Chart):
    """
    >>> PieChart([('Hello', 60), ('World', 40)]).get_url()
    'http://chart.apis.google.com/chart?cht=p&chd=t:60|40&chl=Hello|World&chs=750x375'
    """
    def __init__(self, data, **kwargs):
        try:
            max_options = kwargs.pop('max_options')
        except KeyError:
            max_options = None

        super(PieChart, self).__init__(data, **kwargs)
        self['cht'] = 'p'

        sorted_data = sorted(data, key=lambda p: p[1], reverse=True)
        if max_options is not None and len(sorted_data) > max_options:
            self.__truncate_options(sorted_data, max_options)

        normalized_data = self.__normalize(sorted_data)

        labels, values = unzip(normalized_data)

        self['chd'] = 't:' + ','.join(str(x) for x in values)
        self['chl'] = '|'.join(map(str, labels))

    def __truncate_options(self, sorted_data, max_options):
        "Truncates the data to the number of options given."
        other_value = 0.0
        while len(sorted_data) > max_options - 1:
            other_value += sorted_data.pop()[1]

        sorted_data.append(('Other', other_value))
        return

    def __normalize(self, data):
        total = float(sum(x[1] for x in data))
        return [(l, 100*v/total) for (l, v) in data]

class BaseLineChart(Chart):
    def _axis_from_data(self, values):
        min_value = min(values)
        max_value = max(values)
        tick = (max_value - min_value) / 10.0
        return min_value, max_value, tick

    def _stringify(self, values):
        return ','.join(['%.02f' % v for v in values])

    def _normalize_points(self, old_values, new_range=(0, 100)):
        new_min, new_max = new_range
        new_diff = float(new_max - new_min)

        old_min = min(old_values)
        old_max = max(old_values)
        old_diff = float(old_max - old_min)
        values = [new_min + (x - old_min)*new_diff/old_diff for \
                x in old_values]
        return values

class Transform(object):
    "A vector scaling and offset which can be applied multiple times."
    def __init__(self, target_min, target_max, orig_min, orig_max):
        self.target_min = target_min
        self.target_max = target_max
        self.orig_min = orig_min
        self.orig_max = orig_max

        target_diff = target_max - target_min
        orig_diff = orig_max - orig_min

        self.offset = target_min - orig_min
        self.multiplier = target_diff / float(orig_diff)

    def transform(self, vector):
        return [(v - self.offset)*self.multiplier for v in vector] 

    def axis_spec(self, ticks=10, integer=False):
        if integer:
            tick_diff = _choose_integer_tick(self.orig_min, self.orig_max)
        else:
            tick_diff = (self.orig_max - self.orig_min)/float(ticks)

        return ','.join(map(str, [self.orig_min, self.orig_max, tick_diff]))

    @staticmethod
    def single(target_min, target_max, vector):
        vector_min = min(vector)
        vector_max = max(vector)

        t = Transform(target_min, target_max, vector_min, vector_max)

        return t.transform(vector), t

    @staticmethod
    def many(target_min, target_max, vectors):
        vector_min = min(min(v) for v in vectors)
        vector_max = max(max(v) for v in vectors)
        t = Transform(target_min, target_max, vector_min, vector_max)
        results = []
        for v in vectors:
            results.append(t.transform(v))

        return results, t

class cycle(object):
    def __init__(self, items):
        self.items = items

    def __iter__(self):
        while True:
            for item in self.items:
                yield item

    def take(self, n):
        for item in self:
            yield item
            n -= 1
            if n <= 0:
                break

class SimpleLineChart(BaseLineChart):
    colours = cycle(['000000', '3030ff', 'ff3030', '30ff30'])

    def __init__(self, data, **kwargs):
        super(SimpleLineChart, self).__init__(data, **kwargs)
        self['cht'] = 'lc'
        self.data = data
        norm_vectors, transform = Transform.many(0, 100, data)
        self['chd'] = self._data_string(norm_vectors)
        self['chco'] = ','.join(self.colours.take(len(data)))
        self.transform = transform

    def get_url(self):
        if 'chxt' not in self:
            self.setup_axes()
        return super(SimpleLineChart, self).get_url()

    def setup_axes(self, integer=False, x_min=0):
        self['chxt'] = 'x,y'
        x_max = x_min + len(self.data[0]) - 1
        x_ticks = _choose_integer_tick(0, x_max)
        self['chxr'] = '0,%d,%d,%.02f|1,%s' % (
                x_min,
                x_max,
                x_ticks,
                self.transform.axis_spec(integer=integer)
            )

    def _data_string(self, vectors):
        return 't:' + '|'.join(','.join('%.02f' % v for v in vec) for vec in
                vectors)

class LineChart(BaseLineChart):
    def __init__(self, data, **kwargs):
        self.x_data, self.y_data = unzip(data)
        self.x_axis = ('x_axis' in kwargs) and kwargs.pop('x_axis') or \
                self._axis_from_data(self.x_data)
        self.y_axis = ('y_axis' in kwargs) and kwargs.pop('y_axis') or \
                self._axis_from_data(self.y_data)

        super(LineChart, self).__init__(data, **kwargs)

        self['cht'] = 'lxy'
        self['chxt'] = 'x,y'
        self['chxr'] = self.__setup_axes()

    def __setup_axes(self):
        return '0,%f,%f,%f|1,%f,%f,%f' % (self.x_axis + self.y_axis)

    def __normalize_data(self, x_range=(0,100)):
        x_values = self._normalize_points(self.x_data, new_range=x_range)
        y_values = self._normalize_points(self.y_data)

        return {
                'chd': 't:' + self._stringify(x_values) + '|' + \
                        self._stringify(y_values)
            }

    def get_url(self):
        tmp_chart = Chart(self.data)
        tmp_chart.update(self)
        tmp_chart.update(self.__normalize_data())
        return tmp_chart.get_url()

def _choose_integer_tick(min_value, max_value, max_ticks=10):
    diff = int(max_value - min_value)
    for tick in _iter_ranges():
        if diff / tick <= max_ticks:
            return tick

def _iter_ranges():
    base = [1, 2, 5]
    multiplier = 1
    while True:
        for x in base:
            yield x * multiplier
        multiplier *= 10
    
# vim: ts=4 sw=4 sts=4 et tw=78:
