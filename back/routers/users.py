from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import PublicKeyResponse

router = APIRouter(prefix="/users", tags=["users"])

