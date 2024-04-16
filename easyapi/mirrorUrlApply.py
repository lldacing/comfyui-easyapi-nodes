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


def get_custom_mirrors():
    settings = get_settings()
    base_mirrors = copy.deepcopy(mirror_url)
    if settings and 'huggingface_mirror' in settings:
        base_mirrors[1]['n_url'] = settings['huggingface_mirror']
    if settings and 'rawgithub_mirror' in settings:
        base_mirrors[0]['n_url'] = settings['rawgithub_mirror']
    if settings and 'github_mirror' in settings:
        base_mirrors[0]['n_url'] = settings['github_mirror']
    return base_mirrors


def replace_mirror_url():
    from urllib.parse import urlparse

    def replace_url(url: str):
        u = urlparse(url)
        netloc = u.netloc
        found = False
        user_agent = None
        for mirror in get_custom_mirrors():
            if netloc is not None and len(netloc) > 0 and netloc.lower() == mirror['o_url'] and mirror['n_url'] != 'None':
                u = u._replace(netloc=mirror['n_url'])
                print('[easyapi] origin url: {}, use mirror url: {}'.format(url, u.geturl()))
                if 'u_agent' in mirror:
                    user_agent = mirror['u_agent']
                found = True
                break
        return found, u, user_agent

    import urllib.request
    origin_urlopen = urllib.request.urlopen

    def wrap_urlopen(url, *args, **kwargs):
        """
        implement of lib urllib
        Args:
            url:
            **kwargs:

        Returns:

        """
        if isinstance(url, str):
            found, u, user_agent = replace_url(url)
            if found:
                url = u.geturl()
                data = None
                if user_agent is not None:
                    headers = {'User-Agent': user_agent}
                    if 'data' in kwargs:
                        data = kwargs['data']
                    url = urllib.request.Request(url, data=data, headers=headers)

            return origin_urlopen.__call__(url, *args, **kwargs)
        else:
            # url is urllib.request.Request
            full_url = url.get_full_url()
            found, u, user_agent = replace_url(full_url)
            if found:
                url.full_url = u.geturl()
                if user_agent is not None:
                    if url.headers is not None:
                        url.headers['User-Agent'] = user_agent
                    else:
                        url.headers = {'User-Agent': user_agent}

            return origin_urlopen.__call__(url, *args, **kwargs)

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
            found, u, user_agent = replace_url(url)
            if found:
                kwargs['url'] = u.geturl()
        elif len(args) >= 3:
            url = args[2]
            found, u, user_agent = replace_url(url)
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
            found, u, user_agent = replace_url(url)
            if found:
                kwargs['str_or_url'] = u.geturl()
        elif len(args) >= 3:
            url = args[2]
            found, u, user_agent = replace_url(url)
            if found:
                new_updater = list(args)
                new_updater[2] = u.geturl()
                args = tuple(new_updater)

        return origin_async_request.__call__(*args, **kwargs)

    urllib.request.urlopen = wrap_urlopen
    requests.Session.request = wrap_requests
    aiohttp.ClientSession._request = wrap_aiohttp_requests


def init():
    try:
        replace_mirror_url()
    except Exception as e:
        print("[easyapi] load mirror url replace patch fail, error: {} ".format(e))
