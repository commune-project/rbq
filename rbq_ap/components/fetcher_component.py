"Functions related to HTTP requests."

from typing import Optional, Callable

import requests
from requests_http_signature import HTTPSignatureAuth

from rbq_backend.models import Account


def get(url: str, account: Optional[Account] = None) -> requests.Response:
    "Fetch JSON data from a URL, with HTTP Signatures authorization."
    return requests.get(
        url,
        auth=auth_from_account(account),
        headers={"Accept": "application/activity+json"}
    )


def auth_from_account(account: Optional[Account] = None) -> Optional[Callable]:
    "Generate the HTTP Signatures authenticator of requests."
    def signature_auth(func):
        """
        Authenticator wrapper.
        The HTTP param used in ActivityPub implementations
        differs from the standard one?
        """
        def call(request):
            request = func(request)
            _signature, string = request.headers["Authorization"].split(" ", 1)
            request.headers["Signature"] = string
            del request.headers["Authorization"]
            return request
        return call
    if account:
        return signature_auth(HTTPSignatureAuth(
            key=account.private_key.encode('utf-8'),
            key_id="%s#main-key" % account.ap_id,
            algorithm="rsa-sha256",
            headers=["(request-target)", "host", "date"]
        ))
    else:
        return None


def post(url: str,
         account: Optional[Account] = None,
         json: Optional[dict] = None) -> requests.Response:
    "Send JSON data to a URL, with HTTP Signatures authorization."
    result = requests.post(
        url,
        auth=auth_from_account(account),
        headers={
            "Accept": "application/activity+json",
            "Content-Type": "application/activity+json"},
        json=json)
    return result
