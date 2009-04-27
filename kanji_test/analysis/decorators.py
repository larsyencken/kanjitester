# -*- coding: utf-8 -*-
#
#  decorators.py
#  kanji_test
# 
#  Created by Lars Yencken on 25-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

"""
Custom authentication decorators.
"""

from django import http
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse

def staff_only(view_f):
    "A decorator for limiting request to staff only."
    def wrapper_f(request, **kwargs):
        if not request.user.is_authenticated():
            return http.HttpResponseRedirect(reverse('auth_login'))

        if not request.user.is_staff:
            t = loader.get_template('analysis/forbidden.html')

            return http.HttpResponseForbidden(
                    t.render(RequestContext(request, {})),
                    mimetype="application/xhtml+xml",
                )

        return view_f(request, **kwargs)

    wrapper_f.__name__ = view_f.__name__
    wrapper_f.__doc__ = view_f.__doc__

    return wrapper_f

# vim: ts=4 sw=4 sts=4 et tw=78:
