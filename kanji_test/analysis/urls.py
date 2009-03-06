# -*- coding: utf-8 -*-
#
#  urls.py
#  kanji_test
# 
#  Created by Lars Yencken on 25-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

from django.conf.urls.defaults import *

urlpatterns = patterns('kanji_test.analysis.views',
    url(r'^basic/$', 'basic', name='analysis_basic'),
    url(r'^charts/$', 'chart_dashboard', name='analysis_charts'),
    url(r'^charts/(?P<name>[a-zA-Z_]+)/$', 'chart_dashboard',
        name='analysis_chart'),
    url(r'^data/$', 'data', name='analysis_data_base'),
    url(r'^data/(?P<name>[a-zA-Z_]+)\.(?P<format>[a-z]+)$', 
        'data', name='analysis_data'),
    url(r'^raters/$', 'raters', name='analysis_raters'),
    url(r'^raters/(?P<rater_id>[0-9]+)/$', 'rater_detail', 
            name='analysis_rater_detail'),
    url(r'^pivots/$', 'pivots', name='analysis_pivots'),
    url(r'^pivots/(?P<pivot_type>[wk])/$', 'pivot_detail', 
            name='analysis_pivot_detail'),
)

# vim: ts=4 sw=4 sts=4 et tw=78:

