import requests
from requests_http_signature import HTTPSignatureAuth

from typing import Optional, Callable
from rbq_backend.models import Account

def get(url: str, account: Optional[Account]=None) -> requests.Response:
    return requests.get(
        url,
        auth=auth_from_account(account),
        headers={"Accept": "application/activity+json"}
    )

def auth_from_account(account: Optional[Account]=None) -> Optional[Callable]:
    def signature_auth(func):
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

def post(url: str, account: Optional[Account]=None, json: Optional[dict]=None) -> requests.Response:
    result = requests.post(
        url,
        auth=auth_from_account(account),
        headers={"Accept": "application/activity+json"},
        json=json
    )
    return result
