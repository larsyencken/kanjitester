#!/bin/bash
#
# setEnvironment.sh
#
# Sets the necessary environment variables for the ML Framework to function.
# Don't run this file, instead type:
#   
#   source environmentVars.sh
#
# from shell.
#

export DJANGO_SETTINGS_MODULE='settings'
export PYTHONPATH="$(pwd)"
export FOKS_PATH="$(pwd)"

echo 'Environment variables set'
