from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from .email_utils import send_verification_email
import random

from .auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user
)

router = APIRouter(
    prefix="/api",
    tags=["Login Endpoints"],
    responses={404: {"description": "Not found"}},
)

# TEMP STORE for codes
verification_codes = {}

class LoginPayload(BaseModel):
    email: str
    password: str

class SalesEngineerLoginPayload(BaseModel):
    email: str
    password: str = None  # Optional password

class CodeVerification(BaseModel):
    email: str
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/sales-engineer/login")
async def sales_engineer_login(payload: SalesEngineerLoginPayload):
    """
    Login endpoint specifically for sales engineers.
    Accepts email and optional password.
    If password is not provided, only email verification is required.
    """
    # First check if the user exists
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Email does not exist, contact your administrator")

    # Generate verification code
    code = str(random.randint(1000, 9999))
    verification_codes[payload.email] = code

    # Send verification email
    await send_verification_email(payload.email, code)

    return {"message": "Verification code sent to your email."}

@router.post("/login")
async def login(payload: LoginPayload):
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    code = str(random.randint(1000, 9999))
    verification_codes[payload.email] = code

    await send_verification_email(payload.email, code)

    return {"message": "Verification code sent to your email."}

@router.post("/verify-code", response_model=Token)
async def verify_code(payload: CodeVerification):
    expected_code = verification_codes.get(payload.email)
    if not expected_code or payload.code != expected_code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    user = authenticate_user(payload.email, None)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    verification_codes.pop(payload.email, None)  # Clear used code

    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/dashboard")
async def read_dashboard(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['name']}, welcome to your dashboard!"}
