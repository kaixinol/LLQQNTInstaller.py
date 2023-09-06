from requests import get


def process_url(func):
    def wrapper(self, url):
        if self.use_git_proxy:
            if 'raw.githubusercontent.com' in url or url.endswith('.git'):
                url = 'https://ghproxy.com/' + url
        return func(self, url)

    return wrapper


class Spider:
    def __init__(self, proxy: dict | None = None, use_git_proxy: bool = False):
        self.proxy = proxy if proxy else {}
        self.use_git_proxy = use_git_proxy

    @process_url
    def get_text(self, url: str) -> str | Exception:
        return get(url, proxies=self.proxy).text

    @process_url
    def get_json(self, url: str) -> dict | Exception:
        return get(url, proxies=self.proxy).json()
