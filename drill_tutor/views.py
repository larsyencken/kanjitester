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

from plugins import plugin_helpers

def test_factories(request):
    """Allows the user to generate questions from each factory."""
    context = {}
    if request.method == 'POST':
        if 'query' in request.POST:
            # Render questions for consumption
            query = request.POST['query']
            questions = []
            for plugin in plugin_helpers.load_plugins():
                questions.append(plugin.get_word_question(query))
            _number_questions(questions)
            context['questions'] = questions
            context['query'] = query
        else:
            # Check submitted answers
            pass
            
    return render_to_response("drill_tutor_test_factories.html", context,
            context_instance=RequestContext(request))

def _number_questions(questions):
    for i in xrange(len(questions)):
        questions[i].question_id = i
    
    return
