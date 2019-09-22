from rest_framework.renderers import JSONRenderer


class ActivityStreamsRenderer(JSONRenderer):
    media_type = 'application/activity+json'

    def render(self, data, media_type=None, renderer_context=None):
        if not data:
            return data
        ctx = data.get('@context', [])
        if not isinstance(ctx, list):
            ctx = [ctx]
        ctx = set(ctx)
        ctx.add('https://www.w3.org/ns/activitystreams')
        if "publicKey" in data.keys():
            ctx.add("https://w3id.org/security/v1")
        data['@context'] = list(ctx)
        return super().render(data, renderer_context=renderer_context)


class ActivityStreamsLDJSONRenderer(ActivityStreamsRenderer):
    media_type = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class WebfingerRenderer(JSONRenderer):
    media_type = 'application/jrd+json'
