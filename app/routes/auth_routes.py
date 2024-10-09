from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.schemas import UserCreate, UserResponse, Token
from app.models import User
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.db import get_session
from sqlmodel import select
router = APIRouter()

# Signup Endpoint
@router.post("/signup", response_model=UserResponse)
def signup(user_create: UserCreate, session: Session = Depends(get_session)):
    # Check if user already exists
    user_exists = session.exec(select(User).where(User.email == user_create.email)).first()
    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Hash the password and create user
    hashed_password = get_password_hash(user_create.password)
    new_user = User(username=user_create.username, email=user_create.email, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

# Login Endpoint
#NOTE: You have to tell the frontend developer that he has to send the email in the key of username and should ask from the user the email but put it against the username key in the header.
@router.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)], session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# Token Refresh Endpoint
@router.post("/token/refresh", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_user)):
    access_token = create_access_token(data={"sub": str(current_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# Protected Route
@router.get("/protected-route")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"msg": "You have access", "user": current_user}
