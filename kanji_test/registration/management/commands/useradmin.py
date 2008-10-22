# -*- coding: utf-8 -*-
# 
#  useradmin.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-22.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.core.management.base import CommandError
from django.contrib.auth import models

class Command(NoArgsCommand):
    help = "Allows you to list and delete registered users."
    option_list = NoArgsCommand.option_list + (
            make_option('-l', '--list', action='store_true', dest='list_users',
                help='List all registered users.'),
            make_option('-r', '--remove', action='store', dest='user',
                help='Remove the given user.'),
        )

    def handle_noargs(self, **options):
        if options.get('list_users'):
            for user in models.User.objects.all().order_by('username'):
                print user.username
        
        elif options.get('user'):
            username = options.get('user')
            user = models.User.objects.get(username=username)
            if not user.is_superuser:
                print 'Deleting user %s' % username
                user.delete()
            else:
                print 'Cannot delete user %s -- user is a superuser' % username

        else:
            print 'Invalid usage. Please run `manage.py help useradmin`.'
        
        return