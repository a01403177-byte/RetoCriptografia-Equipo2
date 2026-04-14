##Aqui es donde se valida y dcodifica el token JWT
from functools import lru_cache

import httpx
from jose import JWTError, jwt

from app.config import settings

##Se obitnene las llaves publicas 
@lru_cache(maxsize=1)
def get_jwks() -> dict:
    response = httpx.get(settings.auth_jwks_url, timeout=5.0)
    response.raise_for_status()
    return response.json()

##Aqui se verifica que el toekn sea valido 
def decode_token(token: str) -> dict:
    jwks = get_jwks()
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    key = next((item for item in jwks["keys"] if item.get("kid") == kid), None)

    if not key:
        raise ValueError("Signing key not found")

    try:
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.auth_audience,
            issuer=settings.auth_issuer,
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
