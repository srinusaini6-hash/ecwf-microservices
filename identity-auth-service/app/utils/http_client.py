import httpx


class HTTPClient:

    @staticmethod
    def post(url: str, data: dict, headers=None):
        with httpx.Client(timeout=10) as client:
            response = client.post(
                url,
                json=data,
                headers=headers,
            )

            response.raise_for_status()
            return response.json()