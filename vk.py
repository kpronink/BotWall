import http.cookiejar as cooki
import json
import logging
import urllib
import urllib.parse
from html.parser import HTMLParser
from urllib import request
from urllib.parse import urlparse

import requests
import time


class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url = None
        self.params = {}
        self.in_form = False
        self.form_parsed = False
        self.method = "GET"

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "form":
            if self.form_parsed:
                raise RuntimeError("Second form on page")
            if self.in_form:
                raise RuntimeError("Already in form")
            self.in_form = True
        if not self.in_form:
            return
        attrs = dict((name.lower(), value) for name, value in attrs)
        if tag == "form":
            self.url = attrs["action"]
            if "method" in attrs:
                self.method = attrs["method"].upper()
        elif tag == "input" and "type" in attrs and "name" in attrs:
            if attrs["type"] in ["hidden", "text", "password"]:
                self.params[attrs["name"]] = attrs["value"] if "value" in attrs else ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "form":
            if not self.in_form:
                raise RuntimeError("Unexpected end of <form>")
            self.in_form = False
            self.form_parsed = True

    def error(self, message):
        pass


def auth(email, password, client_id, scope):
    def split_key_value(kv_pair):
        kv = kv_pair.split("=")
        return kv[0], kv[1]

    # Authorization form
    def auth_user(email, password, client_id, scope, opener):

        response = opener.open(
            'http://oauth.vk.com/oauth/authorize?' +
            'redirect_uri=http://oauth.vk.com/blank.html&response_type=token&' +
            'client_id=%s&scope=%s&display=wap' % (client_id, ",".join(scope))
        )
        html_dock = response.read().decode("utf-8")
        parser = FormParser()
        parser.feed(html_dock)
        parser.close()
        if not parser.form_parsed or parser.url is None or "pass" not in parser.params or "email" not in parser.params:
            raise RuntimeError("Something wrong")
        parser.params["email"] = email
        parser.params["pass"] = password
        if parser.method == "POST":
            response = opener.open(parser.url, urllib.parse.urlencode(parser.params).encode())
        else:
            raise NotImplementedError("Method '%s'" % parser.method)
        return response.read(), response.geturl()

    # Permission request form
    def give_access(html_dock, browser):
        parser = FormParser()
        parser.feed(html_dock.decode("utf-8"))
        parser.close()
        if not parser.form_parsed or parser.url is None:
            raise RuntimeError("Something wrong")
        if parser.method == "POST":
            response = browser.open(parser.url, urllib.parse.urlencode(parser.params).encode())
        else:
            raise NotImplementedError("Method '%s'" % parser.method)
        return response.geturl()

    if not isinstance(scope, list):
        scope = [scope]
    opener = request.build_opener(
        request.HTTPCookieProcessor(cooki.CookieJar()),
        request.HTTPRedirectHandler())
    doc, url = auth_user(email, password, client_id, scope, opener)
    if urlparse(url).path != "/blank.html":
        # Need to give access to requested scope
        url = give_access(doc, opener)
    if urlparse(url).path != "/blank.html":
        raise RuntimeError("Expected success here")
    answer = dict(split_key_value(kv_pair) for kv_pair in urlparse(url).fragment.split("&"))
    if "access_token" not in answer or "user_id" not in answer:
        raise RuntimeError("Missing some values in answer")
    return answer["access_token"], answer["user_id"]


class SessionVk(object):

    def __init__(self):
        self.API_URL = 'https://api.vk.com/method/'
        self._method_name = ''

    def make_vk_request(self, method_request):
        response = SessionVk.send_api_request1(self, method_request._method_args, method_request._method_name)

        return response

    def send_api_request1(self, request_vk, method_name):
        url = self.API_URL + method_name + '?'

        for key, value in request_vk.items():
            url += '&' + key + '=' + value

        response = get_response(url)
        return response


class VkApi(object):
    def __init__(self, session, timeout=10, **method_default_args):
        self._session = session
        self._timeout = timeout
        self._method_default_args = method_default_args

    def __getattr__(self, method_name):
        return VkRequest(self, method_name)

    def __call__(self, method_name, **method_kwargs):
        return getattr(self, method_name)(**method_kwargs)


class VkRequest(object):
    __slots__ = ('_api', '_method_name', '_method_args')

    def __init__(self, api, method_name):
        self._api = api
        self._method_name = method_name

    def __getattr__(self, method_name):
        return VkRequest(self._api, self._method_name + '.' + method_name)

    def __call__(self, **method_args):
        self._method_args = method_args
        return self._api._session.make_vk_request(self)


def check_response(response):
    # noinspection PyGlobalUndefined
    global max_count_post
    if response.status_code == 200:
        if 'response' in response.text:
            is_response = True
            code_error = None
            error_msg = None
        else:
            error = json.loads(response.text)['error']
            is_response = False
            code_error = error['error_code']
            error_msg = error['error_msg']
    else:
        is_response = False
        code_error = response.reason
        error_msg = response.reason

    max_count_post = code_error == '214'

    return is_response, code_error, error_msg


def get_response(url, param_return='response'):
    while True:
        try:
            response = requests.get(url)  # verify=False
            time.sleep(1)
            break
        except requests.ConnectionError:
            logging.debug('нет инета, ребутнем ка роутер')

    is_response, code_error, error_msg = check_response(response)

    if is_response:
        _response = json.loads(response.text)[param_return]
    else:
        logging.debug(str(error_msg))
        _response = None

    return _response
