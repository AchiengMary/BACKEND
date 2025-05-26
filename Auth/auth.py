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

# Updated user database with user types
fake_users_db = {
    "alice@company.com": {"name": "Alice", "password": "secret1"},
    "bob@company.com":   {"name": "Bob",   "password": "secret2"},
    "achieng4024mary@gmail.com": {"name": "Achieng", "password": "secret3"}
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/sales-engineer/login")

def verify_salesperson_email(email: str) -> Optional[dict]:
    """
    Verify if the email exists in the Salesperson_Purchaser_Card entity
    Returns the salesperson data if found, None otherwise
    """
    # Special case for testing
    test_emails = {
        "issirandom@gmail.com": {
            "Name": "Random",
            "Code": "TEST001",
            "E_Mail": "issirandom@gmail.com"
        },
        "achieng75mary@gmail.com": {
            "Name": "Achieng",
            "Code": "TEST002",
            "E_Mail": "achieng75mary@gmail.com"
        },
        "joshuamusira01@gmail.com": {
            "Name": "Joshua",
            "Code": "TEST003",
            "E_Mail": "joshuamusira01@gmail.com"
        },
        "omwengandrew12@gmail.com": {
            "Name": "Andrew",
            "Code": "TEST004",
            "E_Mail": "omwengandrew12@gmail.com"
        },
        "raphaelsarota@gmail.com": {
            "Name": "Raphael",
            "Code": "TEST005",
            "E_Mail": "raphaelsarota@gmail.com"
        }
    }
    
    if email in test_emails:
        return test_emails[email]
        
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

def verify_password(plain_password, hashed_password):
    # In development, we're using plaintext passwords, so direct comparison
    # In production, you would use: return pwd_context.verify(plain_password, hashed_password)
    return plain_password == hashed_password

def get_password_hash(password):
    # In development, we're returning plaintext
    # In production, you would use: return pwd_context.hash(password)
    return password

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
