from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app import config
from app.db import get_session
from app.models import User
from sqlmodel import Session, select
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer with the correct token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")  

# Create a password hash
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Verify the password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Create a new JWT token
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

# Decode and verify JWT token
def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Get the current logged-in user
def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    user_id = decode_token(token)
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
