# Auth/routes.py
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# Relative import from auth.py
from .auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

router = APIRouter(
    prefix="/api",
    tags=["Login Endpoints"],
    responses={404: {"description": "Not found"}},
)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class LoginPayload(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=Token)
async def login(payload: LoginPayload):
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/dashboard")
async def read_dashboard(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['name']}, welcome to your dashboard!"}
