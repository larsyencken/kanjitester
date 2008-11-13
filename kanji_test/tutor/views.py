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

from kanji_test.lexicon import models as lexicon_models
from kanji_test.drill import models as api_models
from kanji_test.drill import plugin_api, load_plugins
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
    return render_to_response('tutor/dashboard.html', {},
            context_instance=RequestContext(request))

#----------------------------------------------------------------------------#

@profile_required
def test_factories(request):
    """Allows the user to generate questions from each factory."""
    context = {}
    context['syllabi'] = usermodel_models.Syllabus.objects.all().order_by(
            'tag')
    render = lambda: render_to_response("tutor/test_factories.html",
            context, context_instance=RequestContext(request))

    if request.method != 'POST' or 'syllabus_tag' not in request.POST:
        return render()
        
    syllabus_tag = request.POST['syllabus_tag']
    context['syllabus_tag'] = syllabus_tag
    syllabus = usermodel_models.Syllabus.objects.get(tag=syllabus_tag)

    query = request.POST.get('query')
    context['query'] = query or ''

    if query:
        if len(query) > 1:
            query_item = syllabus.partiallexeme_set.get(surface_set=query)
        else:
            query_item = syllabus.partialkanji_set.get(kanji__kanji=query)
    else:
        query_item = syllabus.get_random_kanji_item()

    # Render questions for consumption
    questions = []
    for plugin in load_plugins():
        if plugin.supports_item(query_item):
            try:
                questions.append(plugin.get_question(query_item, request.user))
            except plugin_api.UnsupportedItem:
                continue
    context['questions'] = questions
    return render()

#----------------------------------------------------------------------------#

@profile_required
def test_answer_checking(request):
    """Checks the answers submitted from a query."""
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('tutor_test'))

    answered_questions = []
    for key in request.POST.keys():
        if key.startswith('question_'):
            question_id = int(key.split('_')[1])
            answer_id = int(request.POST[key])
            answered_questions.append(AnsweredQuestion(question_id, answer_id))
    
    context = {'has_answers': True}
    context['questions'] = answered_questions
    context['syllabi'] = usermodel_models.Syllabus.objects.order_by('tag')
    context['syllabus_tag'] = request.POST.get('syllabus_tag')
    return render_to_response("tutor/test_factories.html", context,
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

#----------------------------------------------------------------------------#
