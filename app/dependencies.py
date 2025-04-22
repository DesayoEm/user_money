from dotenv import load_dotenv
load_dotenv()
import os
load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = os.environ.get('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30)

from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from fastapi.security import HTTPAuthorizationCredentials
from app.auth import oauth2_scheme, SECRET_KEY, ALGORITHM
from app.services.user import user_service
from app.schemas.user import User

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email") or payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Missing email in token.")
    except JWTError as e:
        print("JWT Decode error:", e)
        raise HTTPException(status_code=401, detail="Invalid token")

    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

