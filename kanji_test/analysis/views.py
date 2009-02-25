# -*- coding: utf-8 -*-
#
#  views.py
#  kanji_test
# 
#  Created by Lars Yencken on 25-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

from django.shortcuts import render_to_response
from django.template import RequestContext

from kanji_test.analysis.decorators import staff_only

@staff_only
def analysis_home(request):
    return render_to_response("analysis/home.html", {},
            RequestContext(request))

# vim: ts=4 sw=4 sts=4 et tw=78:

