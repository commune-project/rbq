from rest_framework.renderers import JSONRenderer
from rbq_backend.components.asobject_component import ASDict, filter_asobject_for_output


class ActivityStreamsRenderer(JSONRenderer):
    "Render returned JSON as ActivityStreams."
    media_type = 'application/activity+json'

    def render(self, data: ASDict, accepted_media_type=None, renderer_context=None) -> bytes:
        data = filter_asobject_for_output(data)
        return super().render(
            data,
            accepted_media_type=self.media_type,
            renderer_context=renderer_context)


class ActivityStreamsLDJSONRenderer(ActivityStreamsRenderer):
    media_type = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class WebfingerRenderer(JSONRenderer):
    "Render returned JSON as JRD."
    media_type = 'application/jrd+json'
