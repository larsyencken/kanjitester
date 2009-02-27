# -*- coding: utf-8 -*-
# 
#  settings.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

"""Django settings for kanji_test project."""

from os import path

PROJECT_NAME = 'Kanji Tester'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Location of any additional resources 
#DATA_DIR = ''

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Australia/Melbourne'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

PROJECT_ROOT = path.abspath(path.dirname(__file__))

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path.join(PROJECT_ROOT, '..', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'dc6hz00zcf8wym4hsx0jf-%c)_hq%n)rt55@*!(*3y9^48pj-s'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'kanji_test.context_processors.basic_vars',
)

ROOT_URLCONF = 'kanji_test.urls'

TEMPLATE_DIRS = (
    path.join(PROJECT_ROOT, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'kanji_test.tutor',
    'kanji_test.lexicon',
    'kanji_test.drill',
    'kanji_test.util',
    'kanji_test.registration',
    'kanji_test.user_model',
    'kanji_test.plugins.visual_similarity',
    'kanji_test.plugins.reading_alt',
    'kanji_test.plugins.reading_alt.hierarchy',
    'kanji_test.user_profile',
    'kanji_test.analysis',
    'checksum',
)

TEST_DATABASE_CHARSET = 'utf8'
TEST_DATABASE_COLLATION = 'utf8_general_ci'

CONTROL_DRILL_PLUGINS = (
    'kanji_test.plugins.basic_drills.ReadingQuestionFactory',
    'kanji_test.plugins.basic_drills.SurfaceQuestionFactory',
    'kanji_test.plugins.basic_drills.GlossQuestionFactory',
)

ADAPTIVE_DRILL_PLUGINS = (
    'kanji_test.plugins.reading_alt.ReadingAlternationQuestions',
    'kanji_test.plugins.basic_drills.GlossQuestionFactory',
    'kanji_test.plugins.visual_similarity.VisualSimilarityDrills',
)

DRILL_PLUGINS = list(set(CONTROL_DRILL_PLUGINS + ADAPTIVE_DRILL_PLUGINS))

USER_MODEL_PLUGINS = (
    'kanji_test.plugins.visual_similarity.VisualSimilarity',
    'kanji_test.plugins.reading_alt.KanjiReadingModel',
)

# auth
AUTH_PROFILE_MODULE = 'user_profile.userprofile'

# drill; drill_plugins
N_DISTRACTORS = 5
QUESTIONS_PER_SET = 10
QUESTIONS_PER_PAGE = 5

# visual_similarity
MIN_TOTAL_DISTRACTORS = 15
MAX_GRAPH_DEGREE = MIN_TOTAL_DISTRACTORS

# reading_alt
ALTERNATION_ALPHA = 0.5
VOWEL_LENGTH_ALPHA = 0.05
PALATALIZATION_ALPHA = 0.05
MAX_READING_LENGTH = 30
UTF8_BYTES_PER_CHAR = 3 # For cjk chars

# registration
ACCOUNT_ACTIVATION_DAYS = 15

N_ROWS_PER_INSERT = 10000
DEFAULT_LANGUAGE_CODE = 'eng'
UPDATE_EPSILON = 0.2

# When True, enables the debugging media view.
DEPLOYED = False

DEFAULT_FROM_EMAIL = "Kanji Tester <lljy@csse.unimelb.edu.au>"

GOOGLE_ANALYTICS_CODE = None

# Overwrite any of these settings with local customizations.
try:
    from local_settings import *
except ImportError:
    pass
