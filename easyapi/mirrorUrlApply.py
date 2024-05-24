from enum import Enum

from .settings import get_settings
import copy

mirror_url = [
    {
        "id": "rawgithub",
        "o_url": "raw.githubusercontent.com",
        # "n_url": "raw.gitmirror.com",
        "n_url": "None",
        "u_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
    },
    {
        "id": "huggingface",
        "o_url": "huggingface.co",
        # "n_url": "hf-mirror.com"
        "n_url": "None",
        "u_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    },
    {
        "id": "github",
        "o_url": "github.com",
        # "n_url": "mirror.ghproxy.com/https://github.com"
        "n_url": "None",
        "u_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    },
]
clone_mirror_url = [
    {
        "id": "clone_github",
        "o_url": "github.com",
        # "n_url": "mirror.ghproxy.com/https://github.com"
        "n_url": "None",
        "u_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    },
]


class Mirror(Enum):
    DOWN_MODEL = 0
    GIT_CLONE = 1


def get_custom_mirrors(mirror_type=None):
    settings = get_settings()
    if mirror_type is Mirror.GIT_CLONE:
        base_mirrors = copy.deepcopy(clone_mirror_url)
        if settings and 'clone_github_mirror' in settings:
            base_mirrors[0]['n_url'] = settings['clone_github_mirror']
    elif mirror_type is Mirror.DOWN_MODEL:
        base_mirrors = copy.deepcopy(mirror_url)
        if settings and 'huggingface_mirror' in settings:
            base_mirrors[1]['n_url'] = settings['huggingface_mirror']
        if settings and 'rawgithub_mirror' in settings:
            base_mirrors[0]['n_url'] = settings['rawgithub_mirror']
        if settings and 'github_mirror' in settings:
            base_mirrors[2]['n_url'] = settings['github_mirror']
    else:
        base_mirrors = {}
    return base_mirrors


def replace_mirror_url():
    from urllib.parse import urlparse

    def replace_url(url: str, mirror_type: Mirror = None):
        u = urlparse(url)
        netloc = u.netloc
        found = False
        user_agent = None
        for mirror in get_custom_mirrors(mirror_type):
            if netloc is not None and len(netloc) > 0 and netloc.lower() == mirror['o_url'] and mirror['n_url'] != 'None':
                u = u._replace(netloc=mirror['n_url'])
                print('[easyapi] origin url: {}, use mirror url: {}'.format(url, u.geturl()))
                if 'u_agent' in mirror:
                    user_agent = mirror['u_agent']
                found = True
                break
        return found, u, user_agent

    import urllib.request
    import socket
    # open(self, fullurl, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT)
    origin_urllib_open = urllib.request.OpenerDirector.open

    def wrap_open(obj, fullurl, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        """
        implement of lib urllib
        Args:
            **args: self, fullurl
            **kwargs:

        Returns:

        """
        if isinstance(fullurl, str):
            found, u, user_agent = replace_url(fullurl, Mirror.DOWN_MODEL)
            if found:
                url = u.geturl()
                if user_agent is not None:
                    headers = {'User-Agent': user_agent}
                    url = urllib.request.Request(url, data=data, headers=headers)

                return origin_urllib_open.__call__(obj, url, data, timeout)
            else:
                return origin_urllib_open.__call__(obj, fullurl, data, timeout)

        else:
            # url is urllib.request.Request
            full_url = fullurl.get_full_url()
            found, u, user_agent = replace_url(full_url, Mirror.DOWN_MODEL)
            if found:
                fullurl.full_url = u.geturl()
                if user_agent is not None:
                    if fullurl.headers is not None:
                        fullurl.headers['User-Agent'] = user_agent
                    else:
                        fullurl.headers = {'User-Agent': user_agent}

            return origin_urllib_open.__call__(obj, fullurl, data, timeout)

    import requests
    origin_request = requests.Session.request

    def wrap_requests(*args, **kwargs):
        """
        implement of lib requests
        Args:
            **args: self, method, url
            **kwargs:

        Returns:

        """

        if 'url' in kwargs:
            url = kwargs['url']
            found, u, user_agent = replace_url(url, Mirror.DOWN_MODEL)
            if found:
                kwargs['url'] = u.geturl()
        elif len(args) >= 3:
            url = args[2]
            found, u, user_agent = replace_url(url, Mirror.DOWN_MODEL)
            if found:
                new_updater = list(args)
                new_updater[2] = u.geturl()
                args = tuple(new_updater)

        return origin_request.__call__(*args, **kwargs)

    import aiohttp
    origin_async_request = aiohttp.ClientSession._request

    def wrap_aiohttp_requests(*args, **kwargs):
        """
        implement of lib aiohttp
        Args:
            **args: self, method, str_or_url
            **kwargs:

        Returns:

        """

        if 'str_or_url' in kwargs:
            url = kwargs['str_or_url']
            found, u, user_agent = replace_url(url, Mirror.DOWN_MODEL)
            if found:
                kwargs['str_or_url'] = u.geturl()
        elif len(args) >= 3:
            url = args[2]
            found, u, user_agent = replace_url(url, Mirror.DOWN_MODEL)
            if found:
                new_updater = list(args)
                new_updater[2] = u.geturl()
                args = tuple(new_updater)

        return origin_async_request.__call__(*args, **kwargs)

    import git
    origin_git_clone = git.Repo._clone

    def wrap_git_clone(*args, **kwargs):
        """
        implement of lib git clone
        Args:
            **args: cls, git, url
            **kwargs:

        Returns:

        """

        if 'url' in kwargs:
            url = kwargs['url']
            found, u, user_agent = replace_url(url, Mirror.GIT_CLONE)
            if found:
                kwargs['url'] = u.geturl()
        elif len(args) >= 3:
            url = args[2]
            found, u, user_agent = replace_url(url, Mirror.GIT_CLONE)
            if found:
                new_updater = list(args)
                new_updater[2] = u.geturl()
                args = tuple(new_updater)

        return origin_git_clone.__call__(*args, **kwargs)

    # urllib.request.urlopen = wrap_urlopen
    urllib.request.OpenerDirector.open = wrap_open
    requests.Session.request = wrap_requests
    aiohttp.ClientSession._request = wrap_aiohttp_requests
    git.Repo._clone = wrap_git_clone

    # try:
        # manager has been not loaded
        # from ComfyUI-Manager.glob import manager_core
        # wrap_manager_git_clone = manager_core.gitclone_install
        #
        # def wrap_manager_git_clone(files):
        #     urls = copy.deepcopy(files)
        #     if isinstance(urls, []|list|()):
        #         for i in range(len(urls)):
        #             url = urls[i]
        #             found, u, user_agent = replace_url(url, Mirror.GIT_CLONE)
        #             if found:
        #                 urls[i]=u.geturl()
        #
        #     return wrap_manager_git_clone.__call__(urls)
        #
        # manager_core.gitclone_install = wrap_manager_git_clone
    # except Exception as e:
    #     print("[easyapi] fail to apply manager clone patch, error: {} ".format(e))


def init():
    try:
        replace_mirror_url()
    except Exception as e:
        print("[easyapi] fail to apply mirror url patch, error: {} ".format(e))
