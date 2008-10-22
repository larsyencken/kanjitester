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

from cjktools import scripts
from cjktools.scripts import containsScript, Script

from kanji_test.plugins import plugin_helpers
from kanji_test.lexicon import models as lexicon_models
from kanji_test.plugins.api import models as api_models
from kanji_test.util import html

#----------------------------------------------------------------------------#

def index(request):
    """Render the dashboard interface."""
    if not request.user.is_authenticated():
        return welcome(request)
    
    return render_to_response('drill_tutor_dashboard.html', {},
            context_instance=RequestContext(request))

#----------------------------------------------------------------------------#

def welcome(request):
    """An alternative to the dashboard for users who aren't logged in."""
    return render_to_response('drill_tutor_welcome.html', {},
            context_instance=RequestContext(request))

#----------------------------------------------------------------------------#

def test_factories(request):
    """Allows the user to generate questions from each factory."""
    context = {}
    render = lambda: render_to_response("drill_tutor_test_factories.html",
            context, context_instance=RequestContext(request))
    if request.method != 'POST' or 'query' not in request.POST:
        return render()
        
    query = request.POST['query']
    context['query'] = query

    if not scripts.containsScript(scripts.Script.Kanji, query):
        context['error'] = 'Please enter a query containing kanji.'
        return render()
        
    if len(query) > 1:
        method = 'get_word_question'
        supports_method = 'supports_words'
        if lexicon_models.LexemeSurface.objects.filter(surface=query
                ).count() != 1:
            context['error'] = 'No unique match found.'
            return render()
    else:
        method = 'get_kanji_question'
        supports_method = 'supports_kanji'
        if lexicon_models.Kanji.objects.filter(kanji=query).count() == 0:
            context['error'] = 'No matching kanji found.'
            return render()

    # Render questions for consumption
    questions = []
    for plugin in plugin_helpers.load_plugins():
        if getattr(plugin, supports_method):
            questions.append(getattr(plugin, method)(query))
    context['questions'] = questions
    return render()

#----------------------------------------------------------------------------#

def test_answer_checking(request):
    """Checks the answers submitted from a query."""
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('drill_tutor_test'))

    answered_questions = []
    for key in request.POST.keys():
        if key.startswith('question_'):
            question_id = int(key.split('_')[1])
            answer_id = int(request.POST[key])
            answered_questions.append(AnsweredQuestion(question_id, answer_id))
    
    context = {'has_answers': True}
    context['questions'] = answered_questions
    return render_to_response("drill_tutor_test_factories.html", context,
            context_instance=RequestContext(request))

#----------------------------------------------------------------------------#

class AnsweredQuestion(object):
    """A question and its answer from a user"""
    def __init__(self, question_id, answer_id):
        self.question = api_models.MultipleChoiceQuestion.objects.get(
                id=question_id)
        for attrib in ('question_type', 'pivot_type', 'pivot', 
                'question_plugin'):
            setattr(self, attrib, getattr(self.question, attrib))
        options = []
        for option in self.question.options.all():
            if option.id == answer_id:
                option.is_user_answer = True
                self.is_correct = option.is_correct
            else:
                option.is_user_answer = False
            options.append(option)
        self.options = options
    
        if not self.options:
            raise ValueError('no options were found')
        
        if not hasattr(self, 'is_correct'):
            raise ValueError('answer was not one of the available options')
    
    def _get_stimulus_class(self, stimulus):
        if scripts.scriptType(stimulus) == scripts.Script.Ascii:
            return 'stimulus_roman'
        else:
            return 'stimulus_cjk'
    
    def _get_option_class(self, option_value):
        if scripts.scriptType(option_value) == scripts.Script.Ascii:
            return 'option_choices_roman'
        else:
            return 'option_choices_cjk'
    
    def as_html(self):
        output = []
        output.append(html.P(self.question.instructions,
                **{'class': 'instructions'}))
        if self.is_correct:
            feedback_style = 'success'
            output.append(html.P('Correct', **{'class': feedback_style}))
        else:
            feedback_style = 'failure'
            output.append(html.P('Incorrect', **{'class': feedback_style}))

        if self.question.stimulus:
            output.append(html.P(self.question.stimulus,
                    **{'class': \
                     self._get_stimulus_class(self.question.stimulus)}))
            
        option_choices = []
        question_name = 'question_%d' % self.question.id
        for option in self.options:
            if option_choices:
                option_choices.append(html.BR())
            attribs = {'type': 'radio', 'name': question_name,
                'value': option.id}
            if option.is_user_answer:
                attribs['checked'] = 'checked'
        
            option_choices.append(
                    html.INPUT('&nbsp;' + html.SPAN(option.value,
                            **{'class': self._get_option_class(option.value)}),
                            **attribs)
                )

            if option.is_correct:
                option_choices.append(
                        html.SPAN('&lt;--- correct answer',
                                **{'class': feedback_style}),
                    )
            
        output.append(html.P(*option_choices, **{'class': 'option_choices'}))
        return '\n'.join(output)
