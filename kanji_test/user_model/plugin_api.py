# -*- coding: utf-8 -*-
# 
#  plugin_api.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-24.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import consoleLog
from cjktools import scripts

from kanji_test import settings
from kanji_test.user_model import models

class UserModelPlugin(object):
    """
    A plugin which provides one or more prior distributions across a form
    of user error.
    """
    
    def init_priors(self):
        "Initialises the prior distributions that this plugin provides."
        raise Exception('not implemented')

    def update(self, _response):
        "Updates this error model from a user's response."
        raise Exception('not implemented')

# XXX Needs update to use new alignment format.
class SegmentedSeqPlugin(UserModelPlugin):
    """
    A plugin which uses annotated segments in its options. Requires its
    class to define a "dist_name" attribute, and to define segment annotations
    for all questions and their options.
    """
    def update(self, response):
        "Update our error model from a user's response."
        error_dist = models.ErrorDist.objects.get(user=response.user,
                tag=self.dist_name)
        question = response.question

        if question.pivot_type == 'k':
            self._update_kanji(response, error_dist)

        elif question.pivot_type == 'w':
            self._update_seq(response, error_dist)

        else:
            raise ValueError("unknown question type")

    def _update_kanji(self, response, error_dist):
        "Straight-forward update, no need for annotations."
        question = response.question
        sub_dist = models.ProbDist.from_query_set(
                error_dist.density.filter(condition=question.pivot))
        option_values = [o['value'] for o in \
                question.multiplechoicequestion.options.all().values('value')]
        response_value = response.option.value
        distractors = [v for v in option_values if v != response_value]
        m = max(map(sub_dist.__getitem__, distractors)) + \
                settings.UPDATE_EPSILON
        if m > sub_dist[response_value]:
            sub_dist[response_value] = m
            sub_dist.normalise()
            sub_dist.save_to(error_dist.density, condition=question.pivot)
        return

    def _update_seq(self, response, error_dist):
        "Update using segments and annotations."
        question = response.question
        option_segments = [o['annotation'].split('|') for o in \
                question.multiplechoicequestion.options.values('annotation')]
        response_segments = response.option.annotation.split('|')
        distractors = [ss for ss in option_segments if ss != response_segments]
        for i, char in enumerate(question.annotation.split('|')):
            # Assumption: non-kanji segments are passed through.
            if scripts.scriptType(char) != scripts.Script.Kanji:
                continue

            sub_dist = models.ProbDist.from_query_set(
                    error_dist.density.filter(condition=char))

            m = max(map(sub_dist.__getitem__, [v[i] for v in distractors])) + \
                    settings.UPDATE_EPSILON
            if m > sub_dist[response_segments[i]]:
                sub_dist[response_segments[i]] = m
                sub_dist.normalise()
                sub_dist.save_to(error_dist.density, condition=char)
        return


_cached_plugins = None

def load_plugins():
    """
    Loads the list of plugin classes specified in USER_MODEL_PLUGINS in the
    project settings.
    
    >>> from kanji_test import settings
    >>> len(load_plugins()) == len(settings.USER_MODEL_PLUGINS)
    True
    """
    global _cached_plugins

    if not _cached_plugins:
        plugin_classes = []
        for plugin_path in settings.USER_MODEL_PLUGINS:
            path_parts = plugin_path.split('.')
            base_module = __import__('.'.join(path_parts[:-1]))
            plugin_class = reduce(getattr, path_parts[1:], base_module)
            plugin_classes.append(plugin_class)
        _cached_plugins = dict((c.dist_name, c()) for c in plugin_classes)
    
    return _cached_plugins

def load_priors(syllabus, force=False):
    "Loads the prior distributions represented by each plugin."
    log = consoleLog.default
    log.start('Loading prior distributions', nSteps=2)
    
    log.log('Loading plugins')
    plugins = load_plugins()
  
    log.start('Initialising prior distributions', nSteps=len(plugins))
    for plugin_obj in plugins.itervalues():
        plugin_obj.init_priors(syllabus, force=force)
    log.finish()

    log.finish()

