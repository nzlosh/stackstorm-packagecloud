#!/usr/bin/env python -u

# Licensed to StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional pkg_information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

from st2common.runners.base_action import Action

from lib.packagecloud import create_master_token
from lib.packagecloud import destroy_master_token
from lib.packagecloud import create_read_token
from lib.packagecloud import destroy_read_token
from lib.packagecloud import get_master_token
from lib.packagecloud import get_master_tokens


class ActionManager(Action):

    def run(self, **kwargs):
        '''
        Action runner method
        '''

        http_scheme = 'https'
        api_token = kwargs.pop('api_token')
        api_domain = 'packagecloud.io'
        api_version = 'v1'

        conf = {
            'domain_base': '{}://{}:@{}'.format(
                http_scheme, api_token, api_domain),
            'url_base': '{}://{}:@{}/api/{}'.format(
                http_scheme, api_token, api_domain, api_version),
            'user': kwargs.pop('user'),
            'repo': kwargs.pop('repository'),
        }

        method = kwargs.pop('method')
        conf['verbose'] = not kwargs.get('concise', False)
        conf['debug'] = kwargs.get('debug', False)

        if method == 'create_master_token':
            conf['token_name'] = kwargs.pop('token_name')
            create_master_token(
                conf['user'],
                conf['repo'],
                conf,
                conf['token_name'])
        elif method == 'destroy_master_token':
            conf['token_name'] = kwargs.pop('token_name')
            destroy_master_token(
                conf['user'],
                conf['repo'],
                conf,
                conf['token_name'])
        elif method == 'create_read_token':
            conf['read_token_name'] = kwargs.pop('read_token_name')
            conf['master_token_name'] = kwargs.pop('master_token_name')
            create_read_token(
                conf['master_token_name'],
                conf,
                conf['read_token_name'])
        elif method == 'destroy_read_token':
            conf['read_token_name'] = kwargs.pop('read_token_name')
            conf['master_token_name'] = kwargs.pop('master_token_name')
            destroy_read_token(
                conf['master_token_name'],
                conf,
                conf['read_token_name'])
        elif method == 'get_master_token':
            conf['token_name'] = kwargs.pop('token_name')
            d = get_master_token(
                conf['user'],
                conf['repo'],
                conf['token_name'],
                conf)
            if d is None:
                print("No master token found!", end='')
                exit(1)
            else:
                print(d['value'], end='')

        elif method == 'list_master_token':
            d = get_master_tokens(conf['user'], conf['repo'], conf)
            print('Tokens for %s/%s:' % (conf['user'], conf['repo']))
            for obj in d:
                print('\n  %s (%s)' % (obj['name'], obj['value']))
                print('  read tokens:')
                for robj in obj['read_tokens']:
                    print(
                        '    { id: %s, name: %s, value: %s }' %
                        (robj['id'], robj['name'], robj['value']))
        else:
            print('Unknown method {}'.format(method))
            exit(1)
