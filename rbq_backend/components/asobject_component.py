"Functions related to ASObjects."
from typing import Dict, Optional, Union, List

from django.conf import settings
from rbq_backend import models
from rbq_ap.components import fetcher_component


ASElement = Union[str, int, float, 'ASDict', List['ASElement']]
ASDict = Dict[str, ASElement]

def filter_asobject_for_output(data: ASDict) -> ASDict:
    data = data.copy()
    ctx = data.get('@context', [])
    if not isinstance(ctx, list):
        ctx = [ctx]
    ctx = set(ctx)
    ctx.add('https://www.w3.org/ns/activitystreams')
    if "publicKey" in data.keys():
        ctx.add("https://w3id.org/security/v1")
    data['@context'] = list(ctx)

    if "rbqInternal" in data.keys():
        del data["rbqInternal"]
    return data

def get_asobject(obj: ASDict) -> Optional[models.ASObject]:
    """
    Get an ASObject from database or fetch it, based on its id.

    returns the actual ASObject
    obj["id"] -- the object id IRI.
    """
    return models.ASObject.objects.get_or_fetch(obj)

def save_asobject(obj: ASDict) -> Optional[models.ASObject]:
    return models.ASObject.objects.save_asobject(obj)
