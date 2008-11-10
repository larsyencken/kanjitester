# -*- coding: utf-8 -*-
# 
#  readingDatabase.py
#  foks
#  
#  Created by Lars Yencken on 2007-07-05.
#  Copyright 2007-2008 Lars Yencken. All rights reserved.
# 

"""
Builds the tables of readings and reading alternations.
"""

import sys, optparse
from django.db import connection

from cjktools import scripts
from cjktools.progressBar import withProgress
from cjktools.sequences import groupsOfN
from cjktools.resources import kanjidic
import consoleLog

from kanji_test.user_model_plugins.hierarchy.tree import TreeNode

from reading_model import VoicingAndGeminationModel
from alternation_model import VowelLengthModel, PalatalizationModel

#----------------------------------------------------------------------------#

dependencies = []

_alternation_models = [
    ('voicing and gemination', 's', VoicingAndGeminationModel),
    ('vowel length', 'v', VowelLengthModel),
    ('palatalization', 'p', PalatalizationModel),
]

log = consoleLog.default

#----------------------------------------------------------------------------#

class ReadingDatabase(object):
    """
    Builds the dynamic reading scoring part of the FOKS database.
    """

    #------------------------------------------------------------------------#
    # PUBLIC METHODS
    #------------------------------------------------------------------------#

    @classmethod
    def build(cls):
        """
        Build the tables needed to generate search results at runtime. These
        tables describe readings and reading alternations for each kanji which
        might be searched for.
        """
        log.start('Building reading tables')

        log.log('Detecting unique kanji ', newLine=False)
        sys.stdout.flush()
        kanji_set = cls._get_lookup_kanji()

        alt_tree = cls._build_alternation_tree(kanji_set)

        cls._store_alternation_tree(alt_tree)

        log.log('Storing readings per kanji')
        cls._store_kanji_readings(alt_tree)
        cls._prune_kanji_readings()
        log.finish()

    #------------------------------------------------------------------------#
    # PRIVATE METHODS
    #------------------------------------------------------------------------#

    @staticmethod
    def _get_lookup_kanji():
        """
        Fetches the set of all kanji that require readings for lookup of
        words using FOKS.
        """
        unique_kanji = scripts.uniqueKanji
        kanji_set = set()
        cursor = connection.cursor()
        cursor.execute('SELECT word FROM lexicon_word')
        for (word,) in withProgress(cursor.fetchall(), 100):
            kanji_set.update(unique_kanji(word))
        cursor.close()

        return kanji_set

    #------------------------------------------------------------------------#

    @classmethod
    def _build_alternation_tree(cls, kanji_set):
        """
        Builds the tree of all readings and alternations. Upon completion, any
        possible reading (erroneous or not) for a given kanji should be a leaf
        node in the subtree for that kanji. Each fixed depth in that subtree
        corresponds to an alternation model of some sort.
        """
        log.start('Building alternation tree', nSteps=3)
        log.log('Adding base kanji set')
        root_node = AltTreeNode('root', '/')
        for kanji in kanji_set:
            root_node.add_child(AltTreeNode(kanji, 'k'))

        log.log('Adding good readings')
        kjdic = kanjidic.Kanjidic()
        for kanji_node in root_node.children.values():
            kanji = kanji_node.label
            if kanji in kjdic:
                for reading in kjdic[kanji].all_readings:
                    kanji_node.add_child(AltTreeNode(reading, 'b'))

        log.start('Adding alternation models', nSteps=len(_alternation_models))
        i = 0
        max_len = max(len(n) for (n, c, cl) in _alternation_models)
        pattern = '%%-%ds ' % max_len
        for model_name, model_code, model_class in _alternation_models:
            log.log(pattern % model_name, newLine=False)
            sys.stdout.flush()
            model_obj = model_class.get_cached()
            cls._add_alternation_model(model_obj, model_code, root_node,
                first=(i==0))
            i += 1
        log.finish()

        log.finish()

        return root_node

    #------------------------------------------------------------------------#

    @classmethod
    def _store_alternation_tree(cls, alt_tree):
        """
        Stores the alternation tree to the database using the nested set
        abstraction.
        """
        log.start('Storing alternation tree', nSteps=2)
        # Walk the tree, numbering all nodes.
        log.log('Numbering tree nodes')
        cls._number_tree(alt_tree)

        # Store the tree
        log.log('Storing the tree to the database')
        cls._store_tree(alt_tree)
        log.finish()

    #------------------------------------------------------------------------#

    @classmethod
    def _number_tree(cls, root_node, i=1):
        """
        Numbers the entire tree, as required for the nested set abstraction.

        @return: The update counter
        """
        root_node.left_visit = i
        i += 1

        for child in root_node.children.itervalues():
            i = cls._number_tree(child, i)

        root_node.right_visit = i
        i += 1

        return i

    #------------------------------------------------------------------------#

    @staticmethod
    def _store_tree(root_node):
        """
        Stores the reading alternation tree to the database.
        """
        # Build our list of results.
        def iter_results(tree):
            for node in tree.walk():
                yield (node.label, node.code, node.probability,
                        node.left_visit, node.right_visit)
            return

        # Insert them to the database.
        cursor = connection.cursor()
        cursor.execute('DELETE FROM lexicon_kanjireading')
        cursor.execute('DELETE FROM lexicon_readingalternation')
        max_per_run = 10000
        all_results = iter_results(root_node)

        for results in groupsOfN(max_per_run, all_results):
            cursor.executemany(
                    """
                    INSERT INTO lexicon_readingalternation 
                    (value, code, probability, left_visit, right_visit)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    results,
                )

        cursor.close()
        return

    #------------------------------------------------------------------------#

    @staticmethod
    def _add_alternation_model(model_obj, code, root_node, first=False):
        """
        Adds this alternation model to our current alternation tree. This
        involves walking to each leaf node, then getting all candidates of
        the model, and appending them as new nodes.

        @param model_obj: An alternation model.
        @type model_obj: AlternationModelI
        @param code: A character code for the given alternation.
        @type code: char
        @param root_node: The root node of the entire tree.
        @type root_node: TreeNode
        """
        for kanji_node in withProgress(root_node.children.values()):
            kanji = kanji_node.label
            leaves = list(kanji_node.walk_leaves())
            for reading_node in leaves:
                reading = reading_node.label
                candidates = model_obj.candidates(kanji, reading)
                if not first and candidates == [(reading, 0.0)]:
                    # No changes
                    continue

                for alt_reading, log_prob in candidates:
                    # Only tag changes with their alternation code.
                    if alt_reading == reading:
                        node_code = ''
                    else:
                        node_code = code
                    assert alt_reading not in reading_node.children
                    reading_node.add_child(
                            AltTreeNode(alt_reading, node_code, log_prob))

        return

    #------------------------------------------------------------------------#

    @staticmethod
    def _store_kanji_readings(alt_tree):
        """
        Stores a separate table of only leaf-node readings
        """
        def iter_results(tree):
            for kanji_node in tree.children.itervalues():
                kanji = kanji_node.label

                for leaf_node in kanji_node.walk_leaves():
                    # Calculate the probability for this path.
                    reading = leaf_node.label
                    leaf_path = leaf_node.get_ancestors()[1:]
                    probability = sum([n.probability for n in leaf_path])
                    codes = ''.join([n.code for n in leaf_path])
                    yield (kanji, reading, codes, probability,
                        leaf_path[-1].left_visit)
            return

        max_per_insert = 10000
        all_results = iter_results(alt_tree)
        cursor = connection.cursor()
        cursor.execute('DELETE FROM lexicon_kanjireading')

        for results in groupsOfN(max_per_insert, all_results):
            cursor.executemany(
                    """
                    INSERT INTO lexicon_kanjireading
                    (kanji, reading, alternations, probability,
                        reading_alternation_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    results
                )

        cursor.close()

        return

    #------------------------------------------------------------------------#

    @staticmethod
    def _prune_kanji_readings():
        """Prune duplicates from the database."""
        cursor = connection.cursor()
        cursor.execute(
                """
                SELECT id FROM lexicon_kanjireading AS A
                WHERE A.probability != (
                    SELECT MAX(B.probability) FROM lexicon_kanjireading AS B
                    WHERE A.kanji = B.kanji AND A.reading = B.reading
                )
                """
            )
        ids = cursor.fetchall()
        cursor.executemany(
                """DELETE FROM lexicon_kanjireading WHERE id = %s""",
                ids
        )
        return

    #------------------------------------------------------------------------#

#----------------------------------------------------------------------------#

class AltTreeNode(TreeNode):
    def __init__(self, name, code, probability=0.0):
        TreeNode.__init__(self, label=name,
                attrib={'code': code, 'probability': probability})
        return

    def make_property(name):
        def getter(self):
            return self.attrib[name]
        def setter(self, value):
            self.attrib[name] = value
            return
        return property(getter, setter)

    probability = make_property('probability')
    left_visit = make_property('left_visit')
    right_visit = make_property('right_visit')
    code = make_property('code')

#----------------------------------------------------------------------------#

def build():
    obj = ReadingDatabase()
    obj.build()

#----------------------------------------------------------------------------#
# MODULE EPILOGUE
#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options]

Builds the reading tables required for FOKS lookup."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            default=False, help='Enables debugging mode [False]')

    return parser

#----------------------------------------------------------------------------#

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if args:
        parser.print_help()
        sys.exit(1)

    # Avoid psyco in debugging mode, since it merges stack frames.
    if not options.debug:
        try:
            import psyco
            psyco.profile()
        except:
            pass

    build()
    
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

#----------------------------------------------------------------------------#
  
# vim: ts=4 sw=4 sts=4 et tw=78:
