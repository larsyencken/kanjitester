# -*- coding: utf-8 -*-
# 
#  views.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.conf import settings

from cjktools import scripts
from cjktools.scripts import containsScript, Script

from kanji_test.lexicon import models as lexicon_models
from kanji_test.drill import models as drill_models
from kanji_test.drill import plugin_api, load_plugins, stats
from kanji_test.drill.views import TestSetForm
from kanji_test.user_model import models as usermodel_models
from kanji_test.user_profile.decorators import profile_required
from kanji_test.util import html

#----------------------------------------------------------------------------#

def welcome(request):
    """An alternative to the dashboard for users who aren't logged in."""
    return render_to_response('tutor/welcome.html', {},
            context_instance=RequestContext(request))

#----------------------------------------------------------------------------#

@profile_required
def dashboard(request):
    """Render the dashboard interface."""    
    context = {}
    context['stats'] = stats.get_stats(request.user)
    return render_to_response('tutor/dashboard.html', context,
            context_instance=RequestContext(request))

#----------------------------------------------------------------------------#

@profile_required
def test_user(request):
    """Run a test for the user."""
    context = {'syllabus': request.user.get_profile().syllabus}

    if not 'test_set_id' in request.REQUEST:
        n_questions = settings.QUESTIONS_PER_SET
        if request.method == 'POST' and 'n_questions' in request.POST:
            n_questions = int(request.POST['n_questions'])
        test_set = drill_models.TestSet.from_user(request.user,
                n_questions=n_questions)
        form = TestSetForm(test_set)
    else:
        if request.method != 'POST':
            raise Exception("expected a POST form")
        test_set_id = int(request.REQUEST['test_set_id'])
        test_set = drill_models.TestSet.objects.get(pk=test_set_id)
        form = TestSetForm(test_set, request.POST)

    context['test_set'] = test_set
    context['form'] = form
    context['syllabus'] = request.user.get_profile().syllabus

    return render_to_response('tutor/test_set.html', context,
            context_instance=RequestContext(request))

#----------------------------------------------------------------------------#

@profile_required
def study(request):
    """Study the mistakes made in a test set."""
    context = {}
    if request.method != 'POST' or 'test_set_id' not in request.POST:
        raise Http404
        
    syllabus = request.user.get_profile().syllabus
    
    test_set_id = int(request.POST['test_set_id'])
    test_set = drill_models.TestSet.objects.get(id=test_set_id)
    failed_questions = test_set.questions.all().filter(
            options__is_correct=False)
    
    failed_kanji = failed_questions.filter(pivot_type='k')
    kanji_set = set(o['pivot'] for o in failed_kanji.values('pivot'))
    failed_lexemes = failed_questions.filter(pivot_type='w')
    surface_set = set(o['pivot'] for o in failed_lexemes.values('pivot'))
    
    partial_kanji = usermodel_models.PartialKanji.objects.filter(
            syllabus=syllabus).filter(kanji__in=kanji_set)
    lexeme_set = set(o['lexeme_id'] for o in \
            usermodel_models.PartialLexeme.objects.filter(
            syllabus=syllabus).filter(surface_set__surface__in=surface_set
            ).values('lexeme_id'))
    partial_lexemes = usermodel_models.PartialLexeme.objects.filter(
            syllabus=syllabus).filter(lexeme__id__in=lexeme_set)

    context['partial_kanji'] = partial_kanji
    context['partial_lexemes'] = partial_lexemes
    
    return render_to_response('tutor/study.html', context,
            context_instance=RequestContext(request))
