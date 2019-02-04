#!/usr/bin/env python
"""Packagecloud API module

   Implements functions for working with:
   * master and read-tokens

   Packagecloud API reference docs:
   https://packagecloud.io/docs/api

   Source:
   https://github.com/denisbr/python-packagecloud
"""


from __future__ import print_function

import sys
import time

from requests import ConnectionError
from requests.exceptions import RequestException
from requests import HTTPError
from requests import Request
from requests import Session
from requests import Timeout


def eprint(*args, **kwargs):
    """Print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


def abort(errstr, errcode=1):
    """Print error and exit with errcode"""
    eprint(errstr)
    sys.exit(errcode)


def api_call(url, method, debug, **kwargs):
    """Generic method to make HTTP requests to the packagecloud API

       Will retry on connection error or timeout, until max retries
    """
    resp = None
    attempt = 0
    maxattempts = 3
    req = Request(method.upper(), url, **kwargs)

    if debug:
        print("DEBUG: Request ({}) {}".format(method.upper(), url))

    while True:
        try:
            attempt += 1
            resp = Session().send(
                Session().prepare_request(req), verify=True)
            resp.raise_for_status()
            break
        except (HTTPError, ConnectionError, Timeout) as ex:
            if attempt >= maxattempts:
                abort(ex.response)
            else:
                time.sleep(1)
                continue
        except RequestException as ex:
            abort(ex.response)

    if resp is not None:
        return resp
    else:
        abort("Error making API call to URL: " % url)


###########################################################
# Packagecloud Master tokens                              #
# https://packagecloud.io/docs/api#resource_master_tokens #
###########################################################
def get_master_tokens(config, verbose):
    """Lists all master tokens in repository

       https://packagecloud.io/docs/api#resource_master_tokens_method_index

       GET /api/v1/repos/:user/:repo/master_tokens
    """
    url = "{}/repos/{}/{}/master_tokens".format(
        config['url_base'], config['user'], config['repo'])

    try:
        resp = (api_call(url, 'get', config['debug']))
        tokens = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))

    if verbose:
        print('Tokens for %s/%s:' % (config['user'], config['repo']))
        for obj in tokens:
            print('\n  %s (%s)' % (obj['name'], obj['value']))
            print('  read tokens:')
            for robj in obj['read_tokens']:
                print(
                    '    { id: %s, name: %s, value: %s }' %
                    (robj['id'], robj['name'], robj['value']))

    return tokens


def get_master_token(config, verbose):
    """Get one master token based on name

       https://packagecloud.io/docs/api#resource_master_tokens_method_index

       GET /api/v1/repos/:user/:repo/master_tokens
    """
    url = "{}/repos/{}/{}/master_tokens".format(
        config['url_base'], config['user'], config['repo'])

    try:
        resp = (api_call(url, 'get', config['debug']))
        tokens = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))
    for token in tokens:
        if token['name'] == config['token_name']:
            if verbose:
                print(token['value'], end='')
            return token

    print("No master token found!", end='')
    return None


def create_master_token(config, verbose):
    """Create a named master token in repo

       https://packagecloud.io/docs/api#resource_master_tokens_method_create

       POST /api/v1/repos/:user/:repo/master_tokens
    """
    url = "{}/repos/{}/{}/master_tokens".format(
        config['url_base'], config['user'], config['repo'])
    postdata = ("master_token[name]={}".format(config['token_name']))

    try:
        resp = (api_call(url, 'post', config['debug'], data=postdata))
        token = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))

    if verbose:
        print("Master token {} with value {} created".
              format(token['name'], token['value']), end='')
    else:
        print("{}".format(token['value']), end='')

    return token


def destroy_master_token(config, verbose):
    """Destroy a named master token in repo

       https://packagecloud.io/docs/api#resource_master_tokens_method_destroy

       DELETE /api/v1/repos/:user/:repo/master_tokens/:id
    """
    tokens = get_master_tokens(config, False)

    for token in tokens:
        if token['name'] == config['token_name']:
            if config['debug']:
                print("Found token with name: {}".format(config['token_name']))
            try:
                url = "{}{}".format(config['domain_base'],
                                    token['paths']['self'])
                resp = (api_call(url, 'delete', config['debug']))
            except ValueError as ex:
                abort("Unexpected response from packagecloud API: "
                      "{}".format(str(ex)))
            if resp.status_code == 204:
                if verbose:
                    print(
                        "Token destroyed, name: {}".format(
                            config['token_name']))
                if config['debug']:
                    print("Result: {}" % resp)
            else:
                eprint(
                    "ERROR: Destroying token {} failed".format(
                        config['token_name']))
                eprint("Result: {}".format(resp))

    return True


###########################################################
# Packagecloud Read tokens                                #
# https://packagecloud.io/docs/api#resource_read_tokens   #
###########################################################
def get_read_tokens(mastertoken, config):
    """Lists all read tokens in repository for given master token

       https://packagecloud.io/docs/api#resource_read_tokens_method_index

       GET /api/v1/repos/:user/:repo/master_tokens/
           :master_token/read_tokens.json
    """
    mt_path = mastertoken['paths']['self']
    url = "{}{}/read_tokens.json".\
        format(config['domain_base'], mt_path)

    try:
        resp = (api_call(url, 'get', config['debug']))
        tokens = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))

    return tokens['read_tokens']


def create_read_token(config, verbose):
    """Create a named master token in repo

       https://packagecloud.io/docs/api#resource_read_tokens_method_create

       POST /api/v1/repos/:user/:repo/master_tokens/
            :master_token/read_tokens.json
    """
    config['token_name'] = config['master_token_name']
    mastertoken = get_master_token(config, False)
    if mastertoken is None:
        abort(
            "No master token found for: {}.".format(
                config['master_token_name']))

    mt_path = mastertoken['paths']['self']
    url = "{}{}/read_tokens.json".format(config['domain_base'], mt_path)
    postdata = ("read_token[name]={}".format(config['read_token_name']))

    try:
        resp = (api_call(url, 'post', config['debug'], data=postdata))
        token = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))

    if verbose:
        print("Read token {} with value {} created".
              format(token['name'], token['value']), end='')
    else:
        print("{}".format(token['value']), end='')
    return token['value']


def destroy_read_token(config, verbose):
    """Destroy a named master token in repo

       https://packagecloud.io/docs/api#resource_read_tokens_method_destroy

       DELETE /api/v1/repos/:user/:repo/master_tokens/:id
    """
    config['token_name'] = config['master_token_name']
    mastertoken = get_master_token(config, False)
    if mastertoken is None:
        abort(
            "No master token found for: {}".format(
                config['master_token_name']))

    mt_path = mastertoken['paths']['self']
    tokens = get_read_tokens(mastertoken, config)

    for token in tokens:
        if token['name'] == config['read_token_name']:
            if config['debug']:
                print(
                    "Found token with name: {}".format(
                        config['read_token_name']))
            try:
                url = "{}{}/read_tokens/{}".format(config['domain_base'],
                                                   mt_path, token['id'])
                resp = (api_call(url, 'delete', config['debug']))
            except ValueError as ex:
                abort("Unexpected response from packagecloud API: "
                      "{}".format(str(ex)))
            if resp.status_code == 204:
                if verbose:
                    print("Token destroyed, name: {}".
                          format(config['read_token_name']))
                if config['debug']:
                    print("Result: {}".format(resp))
                return token['value']
            else:
                eprint(
                    "ERROR: Destroying token {} failed".
                    format(config['read_token_name']))
                eprint("Result: {}".format(resp))
