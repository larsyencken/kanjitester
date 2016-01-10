Kanji Tester
============

Status: no longer maintained

OVERVIEW
--------

Kanji Tester is an adaptive testing system for Japanese, which automatically
generates multiple choice questions for learners. This README describes how to
build it from scratch.

For other information, check Kanji Tester's wiki page:

    http://bitbucket.org/larsyencken/kanji-tester/wiki/

or email Lars directly (lars@yencken.org).

PACKAGE DEPENDENCIES
--------------------

Kanji Tester has a number of package dependencies. These are all listed in its
setup.py file. It is not currently designed to be run as an installed package,
so unfortunately you can't install these package dependencies automatically by
simply easy_install'ing kanji tester. Instead, install each of them
individually first.

You also need Scons (a make replacement) and cython installed. To build the C
extensions, simply type "scons" from within the base directory.

DATA DEPENDENCIES
-----------------

A number of data files are required to build Kanji Tester. Currently, they
require a single directory to contain them. Create a file::

    kanji_tester/local_settings.py

to contain your settings for this workspace, and add the path to a data folder
in the DATA_DIR settings, e.g.::

    DATA_DIR = '/home/lars/kanji_test/data'

A number of files are required in the following structure::

    data/
        corpus/
            jp_char_corpus_counts.gz    # kanji frequencies
            jp_word_corpus_counts.gz    # word frequencies
            kanji_readings__edict       # (reading | kanji) frequencies
            kanji_readings__edict.map   # (alternation | kanji, reading) freq.
        syllabus/
            my_syllabus.{chars,words,aligned} # a syllabus to test
        aligned/
            je_edict.aligned.gz         # GP-aligned EDICT entries
        JMdict.gz                       # Japanese-English dictionary

In the future, these would ideally be decoupled somewhat from Kanji Tester. At
the current time, the easiest thing is to email and ask for a copy of this
data bundle, or to download it from the Bitbucket project page, if you have
access.

BUILDING THE DATABASE
---------------------

Kanji Tester also needs MySQL as its database backend. Construct an empty
database for it, and place the settings for accessing the database in::

    kanji_test/local_settings.py

In particular, you need::

    DATABASE_ENGINE = 'mysql'

and also set DATABASE_NAME, DATABASE_USER and DATABASE_PASSWORD appropriately.
Ensure the database is constructed with utf8 as the default encoding, and
utf8_general_ci as the default collation. For example, in mysql, type::

    CREATE DATABASE kanjitest_dev
    DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;

Kanji Tester then needs its initial tables generated. You achieve this by
running::

    source environmentVars.sh
    cd kanji_test
    ./manage.py syncdb
    ./manage.py migrate

At this stage, Kanji Tester will have empty tables. You now need to populate
them::

    ./manage.py build

This step may take a while, and is very database (and disk) intensive. You
should also ensure DEBUG is set to False in local_settings.py, otherwise
memory usage will be very high, since Django stores all database queries in
memory when in debug mode.

When this step is completed, Kanji Tester is ready for use. Note that if the
build is interupted for any reason, you can simply run the build command again
and it will resume where it left off. If you run it on an already built
system, it will only rebuild parts which have changed.

Finally, run::

    ./manage.py runserver

to run the system. You can then find the system at http://localhost:8000/.

- Lars Yencken <lars@yencken.org>
