import requests


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8080/api"):
        self.base_url = base_url

    def _handle(self, response: requests.Response) -> dict:
        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise APIError(detail, response.status_code)
        return response.json()

    def health(self) -> dict:
        r = requests.get(f"{self.base_url}/health", timeout=5)
        return self._handle(r)

    def upload_file(self, file_bytes: bytes, filename: str) -> dict:
        r = requests.post(
            f"{self.base_url}/upload",
            files={"file": (filename, file_bytes)},
            timeout=30,
        )
        return self._handle(r)

    def get_profile(self, session_id: str) -> dict:
        r = requests.get(f"{self.base_url}/profile/{session_id}", timeout=30)
        return self._handle(r)

    def create_chart(self, session_id: str, payload: dict) -> dict:
        r = requests.post(f"{self.base_url}/visualize/{session_id}", json=payload, timeout=30)
        return self._handle(r)

    def get_insights(self, session_id: str) -> dict:
        r = requests.get(f"{self.base_url}/insights/{session_id}", timeout=30)
        return self._handle(r)

    def explain_insights(self, session_id: str, payload: dict) -> dict:
        r = requests.post(f"{self.base_url}/explain/{session_id}", json=payload, timeout=60)
        return self._handle(r)

    def predict(self, session_id: str, payload: dict) -> dict:
        r = requests.post(f"{self.base_url}/predict/{session_id}", json=payload, timeout=120)
        return self._handle(r)


client = APIClient()
