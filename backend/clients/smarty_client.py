import requests
class SmartyClient:
    """Handles all communications with the API"""
    BASE_URL = "https://us-extract.api.smarty.com/"

    def __init__(self, auth_id: str, auth_token: str):
        self.auth_id = auth_id
        self.auth_token = auth_token

    def extract_addresses(self, text: str) -> dict:
        """
        Sends plain text to Smarty's US Extract API and returns the parsed JSON response.
        Raise requests.
        Error if Smarty returns a 2xx Status Code
        """
        params = {
            "auth-id": self.auth_id,
            "auth-token": self.auth_token,
        }
        headers = {
            "Content-Type":"text/plain; charset = utf-8",
        }

        response = requests.post(
            self.BASE_URL,
            params=params,
            headers=headers,
            data=text.encode("utf-8"),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()