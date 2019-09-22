from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from typing import Union

class Key:
    """
    Base class of private and public keys.
    Only used to generate and convert currently.
    """
    def __init__(self, key):
        self.key = key

    def to_pem(self):
        raise NotImplementedError()

    @classmethod
    def from_pem(self, pem):
        raise NotImplementedError()

class PublicKey(Key):

    @classmethod
    def from_pem(cls, pem: Union[str, bytes]) -> 'PublicKey':
        if isinstance(pem, str):
            pem = pem.encode('utf-8')
        key = serialization.load_pem_public_key(
            pem,
            backend=default_backend()
        )
        return cls(key)

    def to_pem(self) -> str:
        return self.key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

class PrivateKey(Key):
    @classmethod
    def generate(cls) -> 'PrivateKey':
        "Generate an RSA private key."
        return cls(rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        ))

    @classmethod
    def from_pem(cls, pem: Union[str, bytes]) -> 'PrivateKey':
        if isinstance(pem, str):
            pem = pem.encode('utf-8')
        key = serialization.load_pem_private_key(
            pem,
            password=None,
            backend=default_backend()
        )
        return cls(key)

    def to_pem(self) -> str:
        return self.key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

    def public_key(self) -> PublicKey:
        "Get public key from a private key pair."
        return PublicKey(self.key.public_key())
