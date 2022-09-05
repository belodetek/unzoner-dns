# -*- coding: utf-8 -*-

import json

from time import sleep
from requests import get
from functools import wraps
from subprocess import Popen, PIPE
from inspect import stack

try:
    from urllib import quote, unquote
except ImportError:
    from urllib.parse import quote, unquote

try:
    from httplib import (NOT_FOUND, OK)
except ImportError:
    from http.client import (NOT_FOUND, OK)

from config import *


def retry(ExceptionToCheck, tries=DEFAULT_TRIES, delay=DEFAULT_DELAY, backoff=DEFAULT_BACKOFF, cdata=None):
    '''Retry calling the decorated function using an exponential backoff.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    '''
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    print(
                        '{}, retrying in {} seconds (mtries={}): {}'.format(
                            repr(e),
                            mdelay,
                            mtries,
                            str(cdata)
                        )
                    )
                    sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry  # true decorator
    return deco_retry


@retry(Exception, cdata='method={}'.format(stack()[0][3]))
def get_node(proto=4, country=TARGET_COUNTRY, client_ip='127.0.0.1'):
    country = quote(country)
    headers = {'X-Auth-Token': API_SECRET}
    try:
        res = get(
            '{}/api/v{}/node/{}/country/{}/geo/{}'.format(
                API_HOST,
                API_VERSION,
                proto,
                country,
                client_ip
            ),
            headers=headers
        )
        if DEBUG: print(res.status_code, res.content)
        if res.status_code in [NOT_FOUND]: return

        try:
            assert res.status_code in [OK]
            try:
                return json.loads(res.content)
            except:
                return res.content
        except:
            res = get(
                '{}/api/v{}/node/{}/country/{}'.format(
                    API_HOST,
                    API_VERSION,
                    proto,
                    country
                ),
                headers=headers
            )
            if DEBUG: print(res.status_code, res.content)
            if res.status_code in [NOT_FOUND]: return

            try:
                assert res.status_code in [OK]
                try:
                    return json.loads(res.content)
                except:
                    return res.content
            except:
                return
    except:
        raise AssertionError((res.status_code, res.content))


@retry(Exception, cdata='method={}'.format(stack()[0][3]))
def run_shell_cmd(cmd):
    shcmd = [unquote(el) for el in cmd.split(' ')]
    if DEBUG: print(shcmd)
    p = Popen(
        shcmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        shell=False
    )
    output, err = p.communicate()
    return p.returncode, output, err


@retry(Exception, cdata='method={}'.format(stack()[0][3]))
def get_ipv(proto=4, host=MGMT_HOST):
    return run_shell_cmd('curl -%s %s' % (proto, host))[1]


@retry(Exception, cdata='method={}'.format(stack()[0][3]))
def get_countries():
    headers = {'X-Auth-Token': API_SECRET}
    res = get(
        '{}/api/v{}/countries/all'.format(
            API_HOST,
            API_VERSION
        ),
        headers=headers
    )
    if DEBUG: print(
        '{}: status_code={} content={}'.format(
            stack()[0][3],
            res.status_code,
            res.content
        )
    )
    if res.status_code not in [OK]:
        raise AssertionError((res.status_code, res.content))
    return res.content
