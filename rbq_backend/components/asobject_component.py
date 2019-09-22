"Functions related to ASObjects."
from rbq_backend import models
from django.conf import settings
from rbq_ap.components import fetcher_component

from typing import Dict, Optional, Any


def get_asobject(obj: Dict[str, Any]) -> Optional[models.ASObject]:
    aso = models.ASObject.objects.get(data__id=obj["id"])
    if aso:
        return aso
    else:
        obj = fetcher_component.get(obj["id"])
        return save_asobject(obj)


def save_asobject(obj: Dict[str, Any]) -> Optional[models.ASObject]:
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


def maybe_create_or_find_context(obj: Dict[str, Any]) -> Dict[str, Any]:
    context = None
    try:
        context = models.ASObject.objects.get(data__id=obj["context"])
        if not context:
            raise Exception("No context")
    except (KeyError, Exception):
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
