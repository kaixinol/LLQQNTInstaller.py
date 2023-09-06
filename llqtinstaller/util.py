from requests import get


class Spider:
    def __init__(self, proxy: dict | None = None):
        self.proxy = proxy if proxy else {}

    def get_text(self, url: str) -> str | Exception:
        return get(url, proxies=self.proxy).text

    def get_json(self, url: str) -> dict | Exception:
        return get(url, proxies=self.proxy).json()
