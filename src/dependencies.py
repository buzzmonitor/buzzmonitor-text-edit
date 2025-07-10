# dependencies.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import config

security = HTTPBasic()

def check_auth(username: str, password: str) -> bool:
    return username == "dev" and password == config.API_KEY

def has_access(credentials: HTTPBasicCredentials = Depends(security)):
    if not check_auth(credentials.username, credentials.password):
        raise HTTPException(status_code=403, detail="Not authenticated")
