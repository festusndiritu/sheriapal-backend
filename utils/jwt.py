import os
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt

# Get values from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "defaultsecretke")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JWT access token. `data` should contain a `sub` claim (e.g. user's email or id).
    Returns the encoded JWT as a string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> dict | None:
    """Verify and decode a JWT. Returns the payload dict if valid, otherwise None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None