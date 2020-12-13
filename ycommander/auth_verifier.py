import hashlib
import base64


def derive_key(password, salt, iterations):
    # type: (str, bytes, int) -> bytes
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, 32)

def auth_verifier(password, salt, iterations):
    derived_key = derive_key(password, salt, iterations)
    derived_key = hashlib.sha256(derived_key).digest()
    au_ver = base64.urlsafe_b64encode(derived_key)
    return au_ver.decode().rstrip('=')

