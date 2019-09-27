AP_URLS = [
    'application/activity+json',
    'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
    # 'application/jrd+json' # Webfinger
]

def accept_routing_middleware(get_response):
    def middleware(request):
        if request.META.get('HTTP_ACCEPT', None) in AP_URLS \
            or request.META.get('CONTENT_TYPE', None) in AP_URLS:
            request.urlconf = 'rbq_ap.urls'

        response = get_response(request)
        return response
    return middleware
