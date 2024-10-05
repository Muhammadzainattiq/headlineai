from sqlmodel import SQLModel

class UserCreate(SQLModel):
    username: str
    email: str
    password: str

class UserLogin(SQLModel):
    email: str 
    password: str

class UserResponse(SQLModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

class Token(SQLModel):
    access_token: str
    token_type: str
