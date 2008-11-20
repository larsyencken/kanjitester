# -*- coding: utf-8 -*-
# 
#  plugin_api.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-24.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import consoleLog

from kanji_test import settings

class UserModelPlugin(object):
    """
    A plugin which provides one or more prior distributions across a form
    of user error.
    """
    
    def init_priors(self):
        "Initialises the prior distributions that this plugin provides."
        raise Exception('not implemented')

    def update(self, response):
        "Updates this error model from a user's response."
        raise Exception('not implemented')

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
        plugin_obj.init_priors(syllabus, force=False)
    log.finish()

    log.finish()

