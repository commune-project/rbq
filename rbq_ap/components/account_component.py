from rbq_backend.models import Account
from urllib.parse import urlparse
from django.core.paginator import Paginator, EmptyPage
from django.db import transaction

from rbq_ap.serializers.actor import ActorSerializer

from rbq_ap.components import fetcher_component, asactivity_component

from typing import Optional, List


def fetch_new_user(ap_id: str, account: Optional[Account] = None) -> Account:
    """
    Fetch a new Actor object from remote server.

    ap_id -- the Actor's ActivityPub id.
    account -- another local Account used to authenticate during the HTTP GET req.
    """
    data = fetcher_component.get(ap_id, account).json()
    domain = urlparse(data["id"]).hostname
    firstname = data["preferredUsername"]
    inbox_uri = None
    try:
        urlparse(data["endpoints"]["sharedInbox"])
        inbox_uri = data["endpoints"]["sharedInbox"]
    except:
        inbox_uri = data["inbox"]
    account = Account(
        username="%s@%s" % (firstname, domain),
        ap_id=data["id"],
        inbox_uri=inbox_uri,
        outbox_uri=data["outbox"],
        following_uri=data["following"],
        followers_uri=data["followers"],
        type=data["type"],
        name=data.get("name", ""),
        summary=data.get("summary", ""),
        url=data.get("url", data["id"]),
        is_locked=data["manuallyApprovesFollowers"],
        public_key=data["publicKey"]["publicKeyPem"]
    )
    account.save()
    return account


def get_or_fetch_user(ap_id: str, account: Optional[Account] = None) -> Account:
    try:
        return Account.objects.get(ap_id=ap_id)
    except Account.DoesNotExist:
        return fetch_new_user(ap_id, account)


def fetch_and_update_user(ap_id: str, account: Optional[Account] = None):
    user = Account.objects.get(ap_id=ap_id)

    data = fetcher_component.get(ap_id, account).json()
    serializer = ActorSerializer(user, data=data)
    if serializer.is_valid():
        return serializer.save()


def _paginator(queryset, page: int) -> List[str]:
    obj_list = Paginator(queryset, 50).page(page).object_list
    return [f.ap_id for f in obj_list]


def gen_followers(account: Optional[Account]) -> dict:
    return {
        "id": account.followers_uri,
        "type": "OrderedCollection",
        "totalItems": account.followers.count(),
        "first": account.followers_uri + "?page=1"
    }


def gen_followers_paged(account: Optional[Account], page: int = 1) -> dict:
    result = {
        "id": account.followers_uri + "?page=%d" % page,
        "type": "OrderedCollection",
        "totalItems": account.followers.count(),
        "partOf": account.followers_uri,
        "next": account.followers_uri + "?page=%d" % (page+1),
        "orderedItems": _paginator(account.followers.all(), page)
    }
    if page > 1:
        result["prev"] = account.followers_uri + "?page=%d" % (page-1)
    try:
        _paginator(account.followers.all(), page+1)
    except EmptyPage:
        return result
    result["next"] = account.followers_uri + "?page=%d" % (page+1)
    return result


def gen_following(account: Optional[Account]) -> dict:
    return {
        "id": account.following_uri,
        "type": "OrderedCollection",
        "totalItems": account.following.count(),
        "first": account.following_uri + "?page=1"
    }


def gen_following_paged(account: Optional[Account], page: int = 1) -> dict:
    result = {
        "id": account.following_uri + "?page=%d" % page,
        "type": "OrderedCollection",
        "totalItems": account.following.count(),
        "partOf": account.following_uri,
        "next": account.following_uri + "?page=%d" % (page+1),
        "orderedItems": _paginator(account.following.all(), page)
    }

    if page > 1:
        result["prev"] = account.following_uri + "?page=%d" % (page-1)
    try:
        _paginator(account.following.all(), page+1)
    except EmptyPage:
        return result
    result["next"] = account.following_uri + "?page=%d" % (page+1)
    return result


def local_follow_user(follower: Account, followee: Account) -> None:
    "Set following relationship locally (Not sending ActivityPub requests)"
    follower.following.add(followee)
    follower.following_count = follower.following.count()
    follower.save()
    followee.followers_count = followee.followers.count()
    followee.save()


def follow_remote_user(follower: Account, followee: Account) -> None:
    "Follow a remote Actor."
    if follower.is_local:
        asactivity_component.send_activity(
            data={
                "type": "Follow",
                "actor": follower.ap_id,
                "object": followee.ap_id,
                "rbqInternal": {
                    "status": "pending"
                }
            },
            recipients=[follower.ap_id, followee.ap_id])
