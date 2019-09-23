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
    try:
        return models.ASObject.objects.get(data__id=obj["id"])
    except models.ASObject.DoesNotExist:
        obj = fetcher_component.get(obj["id"])
        return save_asobject(obj)


def save_asobject(obj: ASDict) -> Optional[models.ASObject]:
    if "id" not in obj.keys():
        return None
    obj = maybe_create_or_find_context(obj)
    try:
        aso = models.ASObject.objects.get(data__id=obj["id"])
        aso.data = obj
        aso.save()
        return aso
    except models.ASObject.DoesNotExist:
        return models.ASObject.objects.create(data=obj)


def maybe_create_or_find_context(obj: ASDict) -> ASDict:
    "Ensure an ActivityStreams object has its context."
    context = None
    try:
        context = models.ASObject.objects.get(data__id=obj["context"])
    except (KeyError, models.ASObject.DoesNotExist):
        if 'inReplyTo' in obj.keys():
            obj["context"] = maybe_create_or_find_context(
                get_asobject({"id": obj["inReplyTo"]}))
        else:
            context = models.ASObject(data={"type": "Context"})
            context.save()
            context.data["id"] = "https://%s/contexts/%s" % (
                settings.RBQ_LOCAL_DOMAINS[0], context.id)
            context.save()
            obj["context"] = context.data["id"]
    return obj
