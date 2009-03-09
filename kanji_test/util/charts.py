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
import operator

from django.utils.http import urlencode
from django.conf import settings
from cjktools.sequences import unzip

_google_charts_url = "http://chart.apis.google.com/chart?"
_default_size = '750x375'

class Chart(dict):
    def __init__(self, data, size=_default_size):
        dict.__init__(self)
        self.data = data
        self['chs'] = size
        self['chco'] = color_desc(len(data))

    def set_size(self, size_spec):
        self['chs'] = size_spec

    def get_url(self):
        # Set label colours to black if possible
        parts = []
        if 'chxs' not in self and 'chxt' in self:
            for i in range(len(self['chxt'].split(','))):
                parts.append('%d,000000' % i)
            self['chxs'] = '|'.join(parts)

        return _google_charts_url + dummy_urlencode(self)

    def get_data(self):
        return self.data

class PieChart(Chart):
    def __init__(self, data, **kwargs):
        try:
            max_options = kwargs.pop('max_options')
        except KeyError:
            max_options = None

        super(PieChart, self).__init__(data, **kwargs)
        self['cht'] = 'p'
        self['chxt'] = 'x'

        sorted_data = sorted(data, key=lambda p: p[1], reverse=True)
        if max_options is not None and len(sorted_data) > max_options:
            self.__truncate_options(sorted_data, max_options)

        normalized_data = self.__normalize(sorted_data)

        labels, values = unzip(normalized_data)

        self['chd'] = 't:' + ','.join(smart_str(x) for x in values)
        self['chl'] = '|'.join(map(smart_str, labels))

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
    def _stringify(self, values):
        return ','.join(['%.02f' % v for v in values])


class SimpleLineChart(BaseLineChart):
    def __init__(self, data, **kwargs):
        super(SimpleLineChart, self).__init__(data, **kwargs)
        self.x_axis = ('x_axis' in kwargs) and kwargs.pop('x_axis') or \
                automatic_axis(range(len(data[0]) + 1))
        self.y_axis = ('y_axis' in kwargs) and kwargs.pop('y_axis') or \
                automatic_axis(*data)
        
        self['cht'] = 'lc'
        self.data = data

        t = Transform(0, 100, self.y_axis[0], self.y_axis[1])
        
        norm_vectors = map(t.transform, data)
        self['chd'] = self._data_string(norm_vectors)
        self.transform = t
        
        self['chxt'] = 'x,y'
        self['chxr'] = '0,%d,%d,%.02f|1,%.02f,%.02f,%.02f' % (
                self.x_axis + self.y_axis
            )

    def _data_string(self, vectors):
        return 't:' + '|'.join(','.join(smart_str(v) for v in vec) for vec in
                vectors)

class LineChart(BaseLineChart):
    def __init__(self, data, **kwargs):
        self.x_data, self.y_data = unzip(data)
        self.x_axis = ('x_axis' in kwargs) and kwargs.pop('x_axis') or \
                automatic_axis(self.x_data)
        self.y_axis = ('y_axis' in kwargs) and kwargs.pop('y_axis') or \
                automatic_axis(self.y_data)

        super(LineChart, self).__init__(data, **kwargs)

        self['cht'] = 'lxy'
        self['chxt'] = 'x,y'
        self['chxr'] = self.__setup_axes()
        self['chco'] = color_desc(1)
        
        x_t = Transform(0, 100, self.x_axis[0], self.x_axis[1], strict=True)
        y_t = Transform(0, 100, self.y_axis[0], self.y_axis[1], strict=True)
        
        x_values = x_t.transform(self.x_data)
        y_values = y_t.transform(self.y_data)
        
        self['chd'] = 't:' + self._stringify(x_values) + '|' + \
                        self._stringify(y_values)

    def __setup_axes(self):
        return '0,%f,%f,%f|1,%f,%f,%f' % (self.x_axis + self.y_axis)

class BarChart(Chart):
    def __init__(self, data, **kwargs):
        labels, points = unzip(data)
        self.y_axis = ('y_axis' in kwargs) and kwargs.pop('y_axis') or \
                automatic_axis(points)

        super(BarChart, self).__init__(data, **kwargs)
        self['cht'] = 'bvg'
        self['chxl'] = '1:' + ('|%s|' % '|'.join(labels))

        self['chxt'] = 'y,x'
        self['chxr'] = '0,%s,%s,%s' % tuple((map(smart_str, self.y_axis)))
        self['chbh'] = 'a'

        t = Transform(0, 100, self.y_axis[0], self.y_axis[1], strict=True)
        norm_points = t.transform(points)

        self['chd'] = 't:' + (','.join(map(smart_str, norm_points)))

#----------------------------------------------------------------------------#

class Transform(object):
    """
    A vector scaling and offset which can be applied multiple times.

    >>> Transform.single(0, 100, [0.0, 0.5, 1.0])[0]
    [0.0, 50.0, 100.0]
    
    >>> t = Transform(0, 1, 1, 2, strict=True)
    >>> result = t.transform([1.1, 1.2])
    >>> abs(result[0] - 0.1) < 1e-8
    True
    >>> abs(result[1] - 0.2) < 1e-8
    True

    >>> t = Transform(0, 1, 1, 2, strict=True)
    >>> t.transform([1.1, 1.2, 3]) #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValueError:
    """
    def __init__(self, target_min, target_max, orig_min, orig_max,
            strict=False):
        self.target_min = target_min
        self.target_max = target_max
        self.orig_min = orig_min
        self.orig_max = orig_max
        self.strict = strict

        target_diff = target_max - target_min
        orig_diff = orig_max - orig_min

        self.offset = target_min - orig_min
        self.multiplier = target_diff / float(orig_diff)

    def transform(self, vector):
        if self.strict:
            checkRange(self.orig_min, self.orig_max, vector)
            
        result = [(v + self.offset)*self.multiplier for v in vector]
        
        if self.strict:
            checkRange(self.target_min, self.target_max, result)
        
        return result

    def axis_spec(self, ticks=10, integer=False):
        if integer:
            tick_diff = choose_integer_tick(self.orig_min, self.orig_max)
        else:
            tick_diff = (self.orig_max - self.orig_min)/float(ticks)

        return ','.join(map(str, [self.orig_min, self.orig_max, tick_diff]))

    @staticmethod
    def single(target_min, target_max, vector, strict=False):
        vector_min = min(vector)
        vector_max = max(vector)

        t = Transform(target_min, target_max, vector_min, vector_max,
                strict=strict)

        return t.transform(vector), t

    @staticmethod
    def many(target_min, target_max, vectors, strict=False):
        vector_min = minmin(vectors)
        vector_max = maxmax(vectors)
        t = Transform(target_min, target_max, vector_min, vector_max,
                strict=strict)
        results = []
        for v in vectors:
            results.append(t.transform(v))

        return results, t
    
    def __repr__(self):
        return '<Transform: offset %f, multiplier %f>' % (
                self.offset, self.multiplier
            )

def automatic_axis(*vectors):
    """
    Returns an automatically determined axis specification for the given 
    values.
    """
    min_value = minmin(vectors)
    max_value = maxmax(vectors)

    if is_all_integer(*vectors):
        return choose_integer_axis(min_value, max_value)
    else:
        return choose_float_axis(min_value, max_value)

def is_all_integer(*vectors):
    for vector in vectors:
        for value in vector:
            if type(value) not in (int, long):
                return False
    
    return True

def choose_float_axis(min_value, max_value):
    """
    Returns a full axis specification for floating point values.
    """
    diff = max_value - min_value
    
    # If within 10% of 0, clamp the minimum value to 0
    if min_value > 0 and min_value < 0.1 * diff:
        min_value = 0.0

    tick = (max_value - min_value) / 10.0
    return min_value, max_value, tick

def choose_integer_axis(min_value, max_value):
    """
    Returns a full axis specification given a minimum and maximum range for
    the original data.
    """
    tick = choose_integer_tick(min_value, max_value)
    if min_value % tick == 0:
        new_min = min_value
    else:
        new_min = tick * (min_value / tick)
        
    if max_value % tick == 0:
        new_max = max_value
    else:
        new_max = tick * ((max_value / tick) + 1)
    
    return new_min, new_max, tick

def choose_integer_tick(min_value, max_value, max_ticks=10):
    """
    >>> choose_integer_tick(0, 20)
    2
    >>> choose_integer_tick(0, 80)
    10
    >>> choose_integer_tick(2000, 2080)
    10
    """
    diff = int(max_value - min_value)
    for tick in _iter_ranges():
        if diff / tick <= max_ticks:
            return tick

def choose_max_value(current_max, multiple=5):
    """
    >>> choose_max_value(7)
    10
    >>> choose_max_value(22.3)
    25
    >>> choose_max_value(76, multiple=10)
    80
    >>> choose_max_value(70, multiple=10)
    70
    """
    if current_max % multiple == 0:
        return current_max
    return ((int(current_max) / multiple) + 1) * multiple

def _iter_ranges():
    """
    Returns a generator for an infinite sequence of salient tick values.
    
    >>> itr = _iter_ranges(); [itr.next() for i in xrange(7)]
    [1, 2, 5, 10, 20, 50, 100]
    """
    base = [1, 2, 5]
    multiplier = 1
    while True:
        for x in base:
            yield x * multiplier
        multiplier *= 10

def smart_str(value):
    """
    Converts basic types to strings, but floating point values with limited
    precision.
    
    >>> smart_str(1)
    '1'
    
    >>> smart_str('dog')
    'dog'
    
    >>> smart_str(10.23421)
    '10.23'
    
    >>> smart_str({})
    Traceback (most recent call last):
        ...
    TypeError: unknown value type
    """
    val_type = type(value)
    if val_type in (int, long):
        return str(value)
    elif val_type == str:
        return value
    elif val_type == unicode:
        return value.encode('utf8')
    elif val_type == float:
        # Fixed decimal precision for charting (after scaling)
        n_sig = '%.02f' % value
        simple = str(value)
        return (len(n_sig) < len(simple)) and n_sig or simple
    else:
        raise TypeError('unknown value type')

def color_desc(n_steps):
    """
    >>> color_desc(1) == to_hex(*_default_start_color)
    True
    >>> color_desc(2).split(',')[1] == to_hex(*_default_end_color)
    True
    """
    return ','.join(interpolate_color(n_steps))

_default_start_color = (30, 30, 255)
_default_end_color = (214, 214, 255)

def interpolate_color(n_steps, start_color=_default_start_color,
        end_color=_default_end_color):
    sr, sg, sb = start_color
    er, eg, eb = end_color

    if n_steps < 1:
        raise ValueError('need at least one colour')

    if n_steps == 1:
        return [to_hex(*start_color)]
    elif n_steps == 2:
        return [to_hex(*start_color), to_hex(*end_color)]

    results = []
    for colour in zip(
                interpolate(sr, er, n_steps),
                interpolate(sg, eg, n_steps),
                interpolate(sb, eb, n_steps),
            ):
        results.append(to_hex(*colour))

    return results

def interpolate(start, end, n_steps):
    """
    >>> interpolate(0, 10, 6)
    [0, 2, 4, 6, 8, 10]
    >>> interpolate(1, 7, 5)
    [1, 2, 4, 5, 7]
    """
    diff = (end - start) / float(n_steps-1)
    eps = 1e-6
    results = []
    for i in xrange(n_steps):
        results.append(int(start + i*diff + eps))

    return results

def to_hex(r, g, b):
    """
    >>> to_hex(48, 48, 255)
    '3030ff'
    >>> to_hex(0, 0, 0)
    '000000'
    """
    results = []
    for c in (r, g, b):
        if c == 0:
            results.append('00')
        else:
            results.append(hex(c).replace('0x', ''))

    return ''.join(results)

def dummy_urlencode(val_dict):
    parts = []
    for key, value in sorted(val_dict.items()):
        parts.append('%s=%s' % (key, value))
    return '&'.join(parts)

def checkRange(start, end, values):
    """
    Checks that the values are within the given range, throwing an exception 
    if any are outside that range.
    
    >>> checkRange(0, 1, [0.2, 0.5]) # succeeds silently
    >>> checkRange(0, 1, [0.2, 2, 0.5])
    Traceback (most recent call last):
        ...
    ValueError: value 2.000000 out of expected range [0.000000, 1.000000]
    """
    for value in values:
        if start > value or end < value:
            raise ValueError('value %f out of expected range [%f, %f]' % (
                value, start, end
            ))

def minmin(vectors):
    return min(min(vec) for vec in vectors)

def maxmax(vectors):
    return max(max(vec) for vec in vectors)


# vim: ts=4 sw=4 sts=4 et tw=78:
