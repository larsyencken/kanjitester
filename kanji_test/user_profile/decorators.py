# -*- coding: utf-8 -*-
#
#  decorators.py
#  kanji_test
# 
#  Created by Lars Yencken on 13-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def profile_required(view_method):
    """
    A decorator which indicates that a user profile is required for the given
    view.
    """
    def maybe_redirect(request):
        user = request.user
        if not user.is_authenticated():
            return HttpResponseRedirect(reverse("tutor_welcome")) 

        if user.userprofile_set.count() == 0:
            return HttpResponseRedirect(reverse("userprofile_profile"))

        return view_method(request)

    return maybe_redirect

# vim: ts=4 sw=4 sts=4 et tw=78:
