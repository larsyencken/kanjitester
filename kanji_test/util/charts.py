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

from django.utils.http import urlencode
from cjktools.sequences import unzip

_google_charts_url = "http://chart.apis.google.com/chart?"
_default_size = '750x375'

class Chart(dict):
    """
    >>> Chart().get_url()
    'http://chart.apis.google.com/chart?chs=750x375'
    """

    def __init__(self, size=_default_size):
        dict.__init__(self)
        self['chs'] = size
        self['chco'] = '3030ff' # blue colour, interpolated

    def get_url(self):
        return _google_charts_url + dummy_urlencode(self)

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

        super(PieChart, self).__init__(**kwargs)
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

class LineChart(Chart):
    def __init__(self, data, **kwargs):
        self.x_data, self.y_data = unzip(data)
        self.x_axis = ('x_axis' in kwargs) and kwargs.pop('x_axis') or \
                self.__axis_from_data(self.x_data)
        self.y_axis = ('y_axis' in kwargs) and kwargs.pop('y_axis') or \
                self.__axis_from_data(self.y_data)

        super(LineChart, self).__init__(**kwargs)

        self['cht'] = 'lxy'
        self['chxt'] = 'x,y'
        self['chxr'] = self.__setup_axes()

    def __axis_from_data(self, values):
        min_value = min(values)
        max_value = max(values)
        tick = (max_value - min_value) / 10.0
        return min_value, max_value, tick

    def __setup_axes(self):
        return '0,%f,%f,%f|1,%f,%f,%f' % (self.x_axis + self.y_axis)

    def __normalize_data(self, x_range=(0,100)):
        x_values = self.__normalize_points(self.x_data, new_range=x_range)
        y_values = self.__normalize_points(self.y_data)

        return {
                'chd': 't:' + self.__stringify(x_values) + '|' + \
                        self.__stringify(y_values)
            }

    def __stringify(self, values):
        return ','.join(['%.02f' % v for v in values])

    def __normalize_points(self, old_values, new_range=(0, 100)):
        new_min, new_max = new_range
        new_diff = float(new_max - new_min)

        old_min = min(old_values)
        old_max = max(old_values)
        old_diff = float(old_max - old_min)
        values = [new_min + (x - old_min)*new_diff/old_diff for \
                x in old_values]
        return values

    def get_url(self):
        tmp_chart = Chart()
        tmp_chart.update(self)
        tmp_chart.update(self.__normalize_data())
        return tmp_chart.get_url()

# vim: ts=4 sw=4 sts=4 et tw=78:
