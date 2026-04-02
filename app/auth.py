"""
Authentication and Authorization module.
Provides dependency injection for verifying hashed API keys via the Authorization header.
"""

import os
import hashlib
import hmac
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Validates the bearer token against the hashed keys provided in the environment.
    Prevents timing attacks using hmac.compare_digest.
    """
    token = credentials.credentials
    
    # Hash the provided token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Get allowed hashes from the environment
    allowed_hashes_str = os.environ.get("ALLOWED_API_KEY_HASHES", "")
    
    if not allowed_hashes_str:
        # Failsafe: If no hashes are configured, drop all authenticated requests 
        # to prevent accidental open access during an environment misconfiguration
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: No allowed API keys configured."
        )
        
    allowed_hashes = [h.strip() for h in allowed_hashes_str.split(",") if h.strip()]
    
    # Compare against allowed hashes securely
    for allowed_hash in allowed_hashes:
        if hmac.compare_digest(token_hash, allowed_hash):
            # Token is valid, return the original token string (can be used for rate limiting bucket)
            return token
            
    # If no matches found, reject
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or unauthorized API Key",
        headers={"WWW-Authenticate": "Bearer"},
    )
