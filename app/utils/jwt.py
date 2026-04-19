import jwt
import os
from datetime import timedelta, datetime, timezone
RANDOM_SECRET = os.getenv("RANDOM_SECRET", "secret")

def create_jwt(data: dict, expire: timedelta):
    expire_time = datetime.now(timezone.utc) + expire
    data.update({"exp": expire_time})
    token = jwt.encode(data, RANDOM_SECRET, algorithm="HS256")
    return token