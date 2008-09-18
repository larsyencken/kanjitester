#!/bin/bash
# 
#  environmentVars.sh
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-18.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 
#  Sets the necessary environment variables for this project to run.
#

export DJANGO_SETTINGS_MODULE='kanji_test.settings'
export PYTHONPATH="$(pwd)"

echo 'Environment variables set'
