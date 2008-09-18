#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  prune_lexicon.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-23.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from kanji_test.lexicon import models

def main():
    print '%d lexemes' % models.Lexeme.objects.all().count()
    n = 0
    for lexeme in models.Lexeme.objects.all():
        if lexeme.sense_set.count() == 0 or \
                lexeme.surface_set.count() == 0 or \
                lexeme.reading_set.count() == 0:
            lexeme.delete()
            n += 1
    
    print '%d deleted' % n

if __name__ == '__main__':
    main()
