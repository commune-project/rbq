from typing import Optional
from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField, CITextField
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.conf import settings

from rbq_backend.components import crypto_component

from .base_models import ARModel
from .administration import Administration

class APActorManagerMixin:
    def gen_ap_id(self, account: 'Account') -> str:
        if account.is_local:
            return "https://%s/users/%s" % (account.domain, account.preferred_username)
        else:
            return account.ap_id
    def gen_inbox_uri(self, account: 'Account') -> str:
        return self.gen_ap_id(account)+"/inbox"
    def gen_outbox_uri(self, account: 'Account') -> str:
        return self.gen_ap_id(account)+"/outbox"
    def gen_following_uri(self, account: 'Account') -> str:
        return self.gen_ap_id(account)+"/following"
    def gen_followers_uri(self, account: 'Account') -> str:
        return self.gen_ap_id(account)+"/followers"
    def set_ap_data(self, account: 'Account'):
        account.ap_id = self.gen_ap_id(account)
        account.inbox_uri = self.gen_inbox_uri(account)
        account.outbox_uri = self.gen_outbox_uri(account)
        account.following_uri = self.gen_following_uri(account)
        account.followers_uri = self.gen_followers_uri(account)

    def set_ap_keys(self, account: 'Account'):
        private_key = crypto_component.PrivateKey.generate()
        public_key = private_key.public_key()
        account.private_key = private_key.to_pem()
        account.public_key = public_key.to_pem()

    def initialize(self, account: 'Account'):
        self.set_ap_data(account)
        account.url = "https://%s/@%s" % (account.domain, account.preferred_username)
        self.set_ap_keys(account)

class AccountManager(UserManager, APActorManagerMixin):
    def get_by_natural_key(self, username):
        return self.get(username__iexact=username)

    def create_superuser(self, username, email, password, **extra_fields):
        _, domain = username.split("@")
        if domain in settings.RBQ_LOCAL_DOMAINS:
            account = super().create_superuser(username, email, password, **extra_fields)
            self.initialize(account)
            account.save()

    def create_user(self, username, email=None, password=None, **extra_fields):
        _, domain = username.split("@")
        if domain in settings.RBQ_LOCAL_DOMAINS:
            account = super().create_user(username, email, password, **extra_fields)
            self.initialize(account)
            account.save()

    @classmethod
    def normalize_email(cls, email: str = None) -> Optional[str]:
        if email is not None:
            return super().normalize_email(email)
        else:
            return None

class SubforumManager(models.Manager, APActorManagerMixin):
    def get_queryset(self):
        "Subforum QuerySet"
        return super().get_queryset().filter(type="Group")

    def create(self, owner: 'Account', **kwargs) -> Optional['Account']:
        if owner.is_local:
            subforum = self.model(type="Group", **kwargs)
            self.initialize(subforum)
            subforum.save()
            Administration(bourgeoisie=owner, proletariat=subforum, admin_type="owner").save()
            return subforum
        else:
            return None

class Account(AbstractBaseUser, PermissionsMixin, ARModel):
    "Customized model for a User (local or remote) or a Subforum"
    AS_TYPES = (
        ('Person', 'Person'),
        ('Service', 'Bot'),
        ('Group', 'Subforum'),
    )

    username = CITextField(unique=True, verbose_name='full username')
    ap_id = models.TextField(unique=True)
    inbox_uri = models.TextField()
    outbox_uri = models.TextField()
    url = models.TextField()
    is_locked = models.BooleanField(default=False)
    name = models.TextField(blank=True, default="", null=True)
    summary = models.TextField(blank=True, default="", null=True)
    type = models.CharField(choices=AS_TYPES, max_length=50, default="Person")
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    email = CITextField(unique=True, null=True, blank=True)
    following = models.ManyToManyField(
        'self',
        related_name='followers',
        symmetrical=False,
        through='Follow', through_fields=('followee', 'follower'))
    following_uri = models.TextField()
    followers_uri = models.TextField()
    public_key = models.TextField()
    private_key = models.TextField(null=True)
    followers_count = models.PositiveIntegerField(null=True)
    following_count = models.PositiveIntegerField(null=True)
    posts_count = models.PositiveIntegerField(null=True)

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']
    @property
    def preferred_username(self):
        username, _ = self.username.split("@")
        return username

    @property
    def domain(self):
        _, domain = self.username.split("@")
        return domain

    @property
    def is_local(self):
        return self.domain in settings.RBQ_LOCAL_DOMAINS

    @property
    def avatar(self):
        return ''

    @property
    def header(self):
        return ''

    @property
    def is_bot(self):
        return self.type == 'Service'
    @is_bot.setter
    def is_bot(self, val):
        if val:
            self.type = 'Service'
        elif self.type == 'Service':
            self.type = 'Person'

    objects = AccountManager()
    subforums = SubforumManager()
