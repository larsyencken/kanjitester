# 
#  SConstruct
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-15.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

"Build instructions for the research codebase."

#----------------------------------------------------------------------------#

import os
from os import path
import sys
from distutils import sysconfig
import py_compile
import re

#----------------------------------------------------------------------------#

# Default include path for python, version inspecific.
scons_python_version = sysconfig.get_config_var('VERSION')
python_version = ARGUMENTS.get('python') or scons_python_version

#----------------------------------------------------------------------------#

def check_libraries(env):
    """ Check whether the correct libraries exist, and thus whether building
        is possible.
    """
    # Detect OS X python installation, and attempt to correct for it.
    if os.uname()[0] == 'Darwin':
        env.Replace(SHLINKFLAGS='$LINKFLAGS -bundle -flat_namespace -undefined suppress')
        env.Replace(SHLIBSUFFIX='.so')
        if os.path.isdir('/opt/local'):
            env.Append(
                    LIBPATH=['/opt/local/lib'],
                    CPPPATH=['/opt/local/include']
                )

    # Detect the presence of necessary dependencies.
    conf = Configure(env)
    env = conf.Finish()

    return env

#----------------------------------------------------------------------------#
# CONFIGURATION
#----------------------------------------------------------------------------#

# Set up the compilation environment.
env = Environment(
        CPPPATH=sysconfig.get_python_inc().replace(scons_python_version,
                python_version),
        LIBPATH=[sysconfig.get_config_var('LIBPL').replace(
                scons_python_version, python_version)],
        SHLIBPREFIX='',
        LIBS=['python%s' % python_version],
    )

environmentVars = (
        'CPATH',
        'LD_LIBRARY_PATH',
        'LIBRARY_PATH',
        'PATH',
    )

envDict = env['ENV']
for var in environmentVars:
    if var in os.environ:
        envDict[var] = os.environ[var]

# Choose between debugging or optimized mode.
if ARGUMENTS.get('debug'):
    print 'Using debug targets'
    env.Replace(DEBUG=True, CXXFLAGS='-O0 -g -Wall ', CFLAGS='-O0 -g -Wall ')
else:
    print 'Using optimised targets'
    env.Replace(DEBUG=False, CXXFLAGS='-O3 -DNDEBUG -Wall ',
           CFLAGS='-O3 -DNDEBUG -Wall ')

# Configure the environment.
env = check_libraries(env)

pyxbuild = Builder(action='cython -o $TARGET $SOURCE')
env.Append(BUILDERS={'Pyrex': pyxbuild})

#----------------------------------------------------------------------------#

SConscript('kanji_test/plugins/visual_similarity/metrics/SConscript',
        exports='env')

#----------------------------------------------------------------------------#
