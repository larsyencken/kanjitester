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

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from kanji_test.user_model import models as usermodel_models
from kanji_test.user_profile import models
from kanji_test.user_model import add_syllabus

@login_required
def create_profile(request):
    "Create a profile if none exists."
    try:
        profile = request.user.get_profile()
    except ObjectDoesNotExist:
        profile = None
    
    if profile is not None:
        # a profile already exists, redirect to a read-only view
        return view_profile(request)

    ProfileForm = _get_profile_form()
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            syllabus = usermodel_models.Syllabus.objects.get(
                    tag=form.cleaned_data['syllabus'])
            profile = models.UserProfile(
                    user=request.user,
                    syllabus=syllabus,
                    first_language=form.cleaned_data['first_language'],
                    second_languages=form.cleaned_data['second_languages'],
                )
            profile.save()
            add_syllabus.add_per_user_models(request.user.username)
            return HttpResponseRedirect(reverse('tutor_dashboard'))
    else:
        form = ProfileForm()
    
    return render_to_response('user_profile/create_profile.html',
            {'form': form}, context_instance=RequestContext(request))

@login_required
def view_profile(request):
    "View an existing profile."
    context = {}
    context['profile'] = request.user.get_profile()
    context['syllabi'] = [s.tag for s in \
            usermodel_models.Syllabus.objects.all()]

    if request.method == 'POST':
        syllabus = usermodel_models.Syllabus.objects.get(
                tag=request.POST['syllabus'])
        profile = request.user.get_profile()
        if syllabus != profile.syllabus:
            profile.syllabus = syllabus
            profile.save()
            add_syllabus.add_per_user_models(request.user.username)
            context['feedback'] = 'Your profile has been updated.'

    return render_to_response('user_profile/view_profile.html',
            context, context_instance=RequestContext(request))

def _get_profile_form():
    syllabus_choices = [(o['tag'], o['tag']) for o in \
            usermodel_models.Syllabus.objects.all().values('tag')]
    class ProfileForm(forms.Form):
        syllabus = forms.ChoiceField(required=True, choices=syllabus_choices,
                help_text="The syllabus you would like to study.")
        first_language = forms.CharField(max_length=100, required=True,
                help_text="Your first language (native or mother tongue).")
        second_languages = forms.CharField(max_length=200, required=False,
                help_text="Any extra languages other than Japanese which you have studied.")

    return ProfileForm

# vim: ts=4 sw=4 sts=4 et tw=78:
