import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file if it exists
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/proposals.db")

# API configuration
API_PREFIX = "/api"
PROJECT_NAME = "Proposal Management API"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# CORS allowed origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
