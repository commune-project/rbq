from typing import Dict, Optional, Any
from rbq_backend.models import Account


def webfinger(resource: str) -> Optional[Dict[str, Any]]:
    "Generate Webfinger response from resource string."
    acct: str = ""
    ap_id: str = ""
    if resource.startswith('acct:'):
        acct = resource
        fullname = resource[len('acct:'):]
        account = Account.objects.get(username=fullname)
        ap_id = account.ap_id
    elif resource.startswith('https://'):
        ap_id = resource
        account = Account.objects.get(ap_id=resource)
        acct = "acct:" + account.username
    else:
        raise Account.DoesNotExist
    return {
        "subject": acct,
        "aliases": [
            ap_id
        ],
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": ap_id
            }
        ]
    }
