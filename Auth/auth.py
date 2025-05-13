from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = "CHANGE_ME"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ERP_BASE_URL = os.getenv("ERP_BASE_URL")
USERNAME = os.getenv("ERP_USERNAME")
PASSWORD = os.getenv("ERP_PASSWORD")

# Now storing plaintext passwords for simplicity (don't do this in prod!)
fake_users_db = {
    "alice@company.com": {"name": "Alice", "password": "secret1"},
    "bob@company.com":   {"name": "Bob",   "password": "secret2"},
    "achieng4024mary@gmail.com": {"name": "Achieng", "password": "secret3"}
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def verify_salesperson_email(email: str) -> Optional[dict]:
    """
    Verify if the email exists in the Salesperson_Purchaser_Card entity
    Returns the salesperson data if found, None otherwise
    """
    # Special case for testing
    if email == "issirandom@gmail.com":
        return {
            "Name": "Test User",
            "Code": "TEST001",
            "E_Mail": "issirandom@gmail.com"
        }
        
    try:
        # URL encode the email as it may contain special characters
        import urllib.parse
        encoded_email = urllib.parse.quote(email)
        
        # Build URL with filter for exact email match
        url = f"{ERP_BASE_URL}/Salesperson_Purchaser_Card?$filter=E_Mail eq '{encoded_email}'"
        
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        if response.status_code == 200:
            data = response.json()
            if data.get('value') and len(data['value']) > 0:
                return data['value'][0]  # Return the first matching salesperson
        return None
    except Exception as e:
        print(f"Error verifying salesperson email: {str(e)}")
        return None

def authenticate_user(email: str, password: str) -> Optional[dict]:
    # First verify if the email exists in the ERP system
    salesperson = verify_salesperson_email(email)
    if not salesperson:
        return None
    
    # If password is provided, verify it (for future use)
    if password is not None:
        # TODO: Implement password verification when needed
        pass
    
    # Return user data from ERP
    return {
        "email": email,
        "name": salesperson.get('Name', ''),
        "code": salesperson.get('Code', ''),
        "type": "sales_engineer"
    }

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "sub": data.get("sub") or data.get("email")})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = authenticate_user(email, None)
    if user is None:
        raise credentials_exception
    return user
