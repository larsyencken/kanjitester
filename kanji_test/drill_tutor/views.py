# -*- coding: utf-8 -*-
# 
#  views.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from cjktools.scripts import containsScript, Script

from plugins import plugin_helpers
from lexicon import models

def test_factories(request):
    """Allows the user to generate questions from each factory."""
    context = {}
    render = lambda: render_to_response("drill_tutor_test_factories.html",
            context, context_instance=RequestContext(request))
    if request.method != 'POST' or 'query' not in request.POST:
        return render()
        
    query = request.POST['query']
    context['query'] = query

    if not containsScript(Script.Kanji, query):
        context['error'] = 'Please enter a query containing kanji.'
        return render()
        
    if len(query) > 1:
        method = 'get_word_question'
        if models.LexemeSurface.objects.filter(surface=query).count() != 1:
            context['error'] = 'No unique match found.'
            return render()
    else:
        method = 'get_kanji_question'
        if models.Kanji.objects.filter(kanji=query).count() == 0:
            context['error'] = 'No matching kanji found.'
            return render()

    # Render questions for consumption
    questions = []
    for plugin in plugin_helpers.load_plugins():
        questions.append(getattr(plugin, method)(query))
    _number_questions(questions)
    context['questions'] = questions
    return render()

def _number_questions(questions):
    for i in xrange(len(questions)):
        questions[i].question_id = i
    
    return
