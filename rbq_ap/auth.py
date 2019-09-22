# rbq_ap/auth.py

from drf_httpsig.authentication import SignatureAuthentication, FAILED
from rbq_backend.models import Account
from rbq_ap.components import account_component

class APSignatureAuthentication(SignatureAuthentication):
    # The HTTP header used to pass the consumer key ID.

    # A method to fetch (User instance, user_secret_string) from the
    # consumer key ID, or None in case it is not found. Algorithm
    # will be what the client has sent, in the case that both RSA
    # and HMAC are supported at your site (and also for expansion).

    required_headers = ["host"]

    def fetch_user_data(self, key_id, algorithm="rsa-sha256"):
        # ...
        # example implementation:
        try:
            ap_id, _key_id = key_id.split("#")
            user = account_component.get_or_fetch_user(ap_id)
            return (user, user.public_key)
        except Account.DoesNotExist:
            return (None, None)

    def authenticate(self, request):
        if "HTTP_SIGNATURE" in request.META.keys():
            request.META["HTTP_AUTHORIZATION"] = "Signature %s" % request.META["HTTP_SIGNATURE"]
            del request.META["HTTP_SIGNATURE"]
        if "CONTENT_LENGTH" in request.META.keys():
            request.META["HTTP_CONTENT_LENGTH"] = request.META["CONTENT_LENGTH"]
        if "CONTENT_TYPE" in request.META.keys():
            request.META["HTTP_CONTENT_TYPE"] = request.META["CONTENT_TYPE"]
        return super().authenticate(request)
