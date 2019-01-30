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
def get_master_tokens(user, repo, config):
    """Lists all master tokens in repository

       https://packagecloud.io/docs/api#resource_master_tokens_method_index

       GET /api/v1/repos/:user/:repo/master_tokens
    """
    url = "{}/repos/{}/{}/master_tokens".format(config['url_base'], user, repo)

    try:
        resp = (api_call(url, 'get', config['debug']))
        tokens = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))

    return tokens


def get_master_tokens_dict(user, repo, config):
    """Get the complete master token dict from packagecloud

       https://packagecloud.io/docs/api#resource_master_tokens_method_index

       GET /api/v1/repos/:user/:repo/master_tokens
    """
    token_list = {}
    tokens = get_master_tokens(user, repo, config)

    for token in tokens:
        # skip the default and web-download keys
        if token['name'] in ('default', 'web-downloads'):
            continue
        if token['name']:
            token_list[token['name']] = token['value']
            if config['debug']:
                print("DEBUG: Found token {} with value {}".
                      format(token['name'], token['value']))

    return token_list


def get_master_token(user, repo, name, config):
    """Get one master token based on name

       https://packagecloud.io/docs/api#resource_master_tokens_method_index

       GET /api/v1/repos/:user/:repo/master_tokens
    """
    url = "{}/repos/{}/{}/master_tokens".format(config['url_base'], user, repo)

    try:
        resp = (api_call(url, 'get', config['debug']))
        tokens = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))
    for token in tokens:
        if token['name'] == name:
            return token

    return None


def create_master_token(user, repo, config, name):
    """Create a named master token in repo

       https://packagecloud.io/docs/api#resource_master_tokens_method_create

       POST /api/v1/repos/:user/:repo/master_tokens
    """
    url = "{}/repos/{}/{}/master_tokens".format(config['url_base'], user, repo)
    postdata = ("master_token[name]={}".format(name))

    try:
        resp = (api_call(url, 'post', config['debug'], data=postdata))
        token = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))

    if config['debug']:
        print("DEBUG: Token {} created, with value {}".
              format(token['name'], token['value']))

    return token


def destroy_master_token(user, repo, config, name):
    """Destroy a named master token in repo

       https://packagecloud.io/docs/api#resource_master_tokens_method_destroy

       DELETE /api/v1/repos/:user/:repo/master_tokens/:id
    """
    tokens = get_master_tokens(user, repo, config)

    for token in tokens:
        if token['name'] == name:
            print("Found token with name: {}".format(name))
            try:
                url = "{}{}".format(config['domain_base'],
                                    token['paths']['self'])
                resp = (api_call(url, 'delete', config['debug']))
            except ValueError as ex:
                abort("Unexpected response from packagecloud API: "
                      "{}".format(str(ex)))
            if resp.status_code == 204:
                print("Token destroyed, name: {}".format(name))
                print("Result: {}" % resp)
            else:
                eprint("ERROR: Destroying token {} failed".format(name))
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


def get_read_tokens_dict(mastertoken, config):
    """Get the complete read token dict for given master token

    """
    token_list = {}
    tokens = get_read_tokens(mastertoken, config)

    for token in tokens:
        if token['name']:
            token_list[token['name']] = token['value']
            if config['debug']:
                print("DEBUG: Found token {} with value {}".
                      format(token['name'], token['value']))

    return token_list


def create_read_token(master_token_name, config, read_token_name):
    """Create a named master token in repo

       https://packagecloud.io/docs/api#resource_read_tokens_method_create

       POST /api/v1/repos/:user/:repo/master_tokens/
            :master_token/read_tokens.json
    """
    mastertoken = get_master_token(config['user'], config['repo'],
                                   master_token_name, config)
    if mastertoken is None:
        abort("No master token found for: {}.".format(master_token_name))

    mt_path = mastertoken['paths']['self']
    url = "{}{}/read_tokens.json".\
        format(config['domain_base'], mt_path)
    postdata = ("read_token[name]={}".format(read_token_name))

    try:
        resp = (api_call(url, 'post', config['debug'], data=postdata))
        token = resp.json()
    except ValueError as ex:
        abort("Unexpected response from packagecloud API: "
              "{}".format(str(ex)))

    if config['debug']:
        print("DEBUG: Token {} created, with value {}".
              format(token['name'], token['value']))
    return token['value']


def destroy_read_token(master_token_name, config, read_token_name):
    """Destroy a named master token in repo

       https://packagecloud.io/docs/api#resource_read_tokens_method_destroy

       DELETE /api/v1/repos/:user/:repo/master_tokens/:id
    """
    mastertoken = get_master_token(
        config['user'],
        config['repo'],
        master_token_name,
        config)
    if mastertoken is None:
        abort("No master token found for: {}".format(master_token_name))

    mt_path = mastertoken['paths']['self']
    tokens = get_read_tokens(mastertoken, config)

    for token in tokens:
        if token['name'] == read_token_name:
            print("Found token with name: {}".format(read_token_name))
            try:
                url = "{}{}/read_tokens/{}".format(config['domain_base'],
                                                   mt_path, token['id'])
                resp = (api_call(url, 'delete', config['debug']))
            except ValueError as ex:
                abort("Unexpected response from packagecloud API: "
                      "{}".format(str(ex)))
            if resp.status_code == 204:
                print("Token destroyed, name: {}".format(read_token_name))
                print("Result: {}".format(resp))
                return token['value']
            else:
                eprint(
                    "ERROR: Destroying token {} failed".
                    format(read_token_name))
                eprint("Result: {}".format(resp))


###########################################################
# Packagecloud Packages                                   #
# https://packagecloud.io/docs/api#resource_stats         #
###########################################################
def get_all_packages(user, repo, config):
    """List All Packages (not grouped by package version)

       https://packagecloud.io/docs/api#resource_packages_method_all

       GET /api/v1/repos/:user/:repo/packages.json
    """
    packages = []
    total = 1
    fetched = 0
    offset = 1

    while fetched < total:
        url = "{}/repos/{}/{}/packages.json?page={}".format(config['url_base'],
                                                            user, repo, offset)
        try:
            resp = (api_call(url, 'get', config['debug']))
            packages = packages + resp.json()
            total = int(resp.headers['Total'])
            perpage = int(resp.headers['Per-Page'])
            fetched += perpage
            offset += 1

        except ValueError as ex:
            abort("Unexpected response from packagecloud API: "
                  "{}".format(str(ex)))

    return packages
