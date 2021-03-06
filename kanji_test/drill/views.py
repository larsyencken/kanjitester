# -*- coding: utf-8 -*-
#
#  views.py
#  kanji_test
# 
#  Created by Lars Yencken on 16-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

import re
import datetime
import random

from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.encoding import force_unicode

from kanji_test.drill import models

class QuestionField(forms.ChoiceField):
    def __init__(self, question):
        options = list(question.options.all())
        random.shuffle(options)
        super(QuestionField, self).__init__(
                choices=tuple([
                        (unicode(opt.id), unicode(opt.value))\
                        for opt in options
                    ]),
                widget=forms.RadioSelect,
                help_text=question.instructions,
                label=question.stimulus,
            )

# XXX could be cleaned up a bit, perhaps using suggestions from:
# http://jacobian.org/writing/dynamic-form-generation/
class TestSetForm(forms.Form):
    def __init__(self, test_set, *args, **kwargs):
        "Builds a test-set-specific form."
        super(TestSetForm, self).__init__(*args, **kwargs)
        self.test_set = test_set
        self.label_suffix = None
        self.ordered_questions = self.test_set.ordered_questions
        self.question_map = {}
        self.n_correct = None
        self.n_unknown = None

        random.seed(test_set.random_seed)
        for question in self.ordered_questions:
            question_key = 'question_%d' % question.id
            self.question_map[question_key] = question
            self.fields[question_key] = QuestionField(question)

        # Are we fully answered?
        if self.is_valid():
            self._save_responses()
            self.has_answers = True
        else:
            self.has_answers = False

    def _save_responses(self):
        "Saves the user's responses to the test set questions."
        assert self.is_valid()
        chosen_option_ids, question_ids, user_responses = \
                self._record_responses()
        options = self._score_responses(question_ids, user_responses)
        return

    def _record_responses(self):
        self.test_set.responses.all().delete()
        chosen_option_ids = set()
        question_ids = []
        user_responses = {}
        for key, value in self.cleaned_data.iteritems():
            if not key.startswith('question_'):
                continue
            option_id = int(value)
            chosen_option_ids.add(option_id)
            question_id = int(key.split('_')[1])
            question_ids.append(question_id)
            user_responses[question_id] = option_id
            self.test_set.responses.create(
                    option_id=option_id,
                    question_id=question_id,
                    user_id=self.test_set.user_id,
                )

        self.test_set.end_time = datetime.datetime.now()
        self.test_set.save()
        return chosen_option_ids, question_ids, user_responses

    def _score_responses(self, question_ids, user_responses):
        n_correct = 0
        n_questions = 0
        options = models.MultipleChoiceOption.objects.filter(
                question__id__in=question_ids)
        response_options = set(user_responses.values())
        for option in options:
            if option.id not in response_options:
                continue
            question_key = 'question_%d' % option.question_id
            self.fields[question_key].is_correct = option.is_correct
            if option.is_correct:
                n_correct += 1
            n_questions += 1
        self.n_correct = n_correct
        self.n_questions = n_questions
        return options

    def as_table(self):
        "Returns an html table representation of this test set."
        return mark_safe(self._html_output(
                # normal row
                """<tr><td class="test-set"><div class="instructions">%(help_text)s</div><div class="stimulus-cjk">%(label)s</div><div class="mc-select">%(field)s</div>%(errors)s""",
                # correct row
                """<tr class="correct"><td class="test-set"><div class="instructions">%(help_text)s</div><div class="success">Correct</div><div class="stimulus-cjk">%(label)s</div><div class="mc-select">%(field)s</div>%(errors)s""",
                # incorrect row
                """<tr class="incorrect"><td class="test-set"><div class="instructions">%(help_text)s</div><div class="failure">Incorrect</div><div class="stimulus-cjk">%(label)s</div><div class="mc-select">%(field)s</div>%(errors)s""",
                # error row
                u'<tr><td colspan="2" class="error">%s</td></tr>',
                # row ender
                '</td></tr>', 
                # help text html
                u'%s', 
                False
            ))

    def as_p(self):
        raise Exception("not supported")

    def as_ul(self):
        raise Exception("not supported")

    def _html_output(self, normal_row, correct_row, incorrect_row, error_row,
            row_ender, help_text_html, errors_on_separate_row):
        """
        Helper function for outputting HTML. Used by as_table(), as_ul(),
        as_p(). Copied almost entirely from its super-class method."
        """
        # Errors that should be displayed above all fields.
        top_errors = self.non_field_errors()
        had_unanswered_questions = False

        output, hidden_fields = [], []
        for name, field in self.fields.items():
            bf = forms.forms.BoundField(self, field, name)

            # Escape and cache in local variable.
            bf_errors = self.error_class([escape(error) for error in \
                    bf.errors])

            if bf.is_hidden:
                if bf_errors:
                    top_errors.extend([u'(Hidden field %s) %s' % (name, \
                            force_unicode(e)) for e in bf_errors])
                hidden_fields.append(unicode(bf))
            else:
                if errors_on_separate_row and bf_errors:
                    output.append(error_row % force_unicode(bf_errors))
                if bf.label:
                    label = escape(force_unicode(bf.label))
                    # Only add the suffix if the label does not end in
                    # punctuation.
                    if self.label_suffix:
                        if label[-1] not in ':?.!':
                            label += self.label_suffix
                    label = bf.label_tag(label) or ''
                else:
                    label = ''
                if field.help_text:
                    help_text = help_text_html % force_unicode(field.help_text)
                else:
                    help_text = u''

                # Custom code for testing field correctness
                field_output = unicode(bf)
                if hasattr(field, 'is_correct'):
                    template = (field.is_correct and correct_row or \
                            incorrect_row)
                    field_output = re.sub(
                            u'<input ',
                            u'<input disabled="disabled" ',
                            field_output,
                            re.UNICODE
                        )
                else:
                    template = normal_row

                errors = force_unicode(bf_errors)
                if "This field is required." in errors:
                    had_unanswered_questions = True
                    
                errors = errors.replace(
                        "This field is required.",
                        "Please answer this question.",
                    )
                output.append(template % {
                            'errors': errors,
                            'label': force_unicode(label),
                            'field': field_output,
                            'help_text': help_text
                        })

        if had_unanswered_questions:
            output.insert(0, error_row % u"You forgot to answer one or more questions. Please answer them before continuing.")
        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))
        if hidden_fields: # Insert any hidden fields in the last row.
            str_hidden = u''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)
        return mark_safe(u'\n'.join(output))

# vim: ts=4 sw=4 sts=4 et tw=78:
