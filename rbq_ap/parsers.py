from rest_framework.parsers import JSONParser

class ActivityStreamsParser(JSONParser):
    media_type = 'application/activity+json'