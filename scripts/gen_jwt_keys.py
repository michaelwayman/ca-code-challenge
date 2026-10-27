"""Print a dev RS256 keypair as .env lines (PEM with literal \\n, single line each). Dev/demo only."""
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
private = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
public = key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()


def line(name, pem):
    return f'{name}="{pem.strip().replace(chr(10), chr(92) + "n")}"'


print(line("AUTH_JWT_PRIVATE_KEY", private))
print(line("APP_JWT_PUBLIC_KEY", public))
