# -*- coding: utf-8 -*-
#
#  views.py
#  kanji_test
# 
#  Created by Lars Yencken on 13-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Views for the user_profile app.
"""

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from kanji_test.user_model import models as usermodel_models
from kanji_test.util.url import urlquote
from kanji_test.user_profile import models
from kanji_test.user_model import add_syllabus

@login_required
def create_profile(request):
    ProfileForm = _get_profile_form()
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            syllabus = usermodel_models.Syllabus.objects.get(
                    tag=form.cleaned_data['syllabus'])
            profile = models.UserProfile(user=request.user,
                    syllabus=syllabus)
            profile.save()
            add_syllabus.add_per_user_models(request.user.username)
            return HttpResponseRedirect(reverse('drilltutor_dashboard'))
    else:
        form = ProfileForm()
    
    return render_to_response('user_profile/create_profile.html',
            {'form': form}, context_instance=RequestContext(request))

def _get_profile_form():
    syllabus_choices = [(o['tag'], o['tag']) for o in \
            usermodel_models.Syllabus.objects.all().values('tag')]
    class ProfileForm(forms.Form):
        syllabus = forms.ChoiceField(required=True, choices=syllabus_choices)

    return ProfileForm

# vim: ts=4 sw=4 sts=4 et tw=78:
