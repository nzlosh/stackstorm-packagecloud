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
            'verbose': not kwargs.get('concise', False),
            'debug': kwargs.get('debug', False),
            'token_name': kwargs.get('token_name'),
            'read_token_name': kwargs.get('read_token_name'),
            'master_token_name': kwargs.get('master_token_name'),
        }

        funcs = {
            'create_master_token': create_master_token,
            'destroy_master_token': destroy_master_token,
            'create_read_token': create_read_token,
            'destroy_read_token': destroy_read_token,
            'get_master_token': get_master_token,
            'list_master_token': get_master_tokens,
        }

        function = kwargs.pop('function')

        # Call the function
        rv = funcs[function](conf, conf['verbose'])
