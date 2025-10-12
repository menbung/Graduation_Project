import requests

class ServerClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout

    def post_results(self, endpoint: str, payload: dict):
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
