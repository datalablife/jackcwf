#!/usr/bin/env python3
"""Generate JWT token for testing API integration."""

import jwt
import json
from datetime import datetime, timedelta
import os
import sys

# Get JWT secret from environment or use default
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHMS", "HS256").split(",")[0].strip()

# Create JWT token
payload = {
    "sub": "test_user",  # subject (user ID)
    "user_id": "test_user",
    "exp": datetime.utcnow() + timedelta(hours=24),  # Expires in 24 hours
    "iat": datetime.utcnow(),  # Issued at
}

try:
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    print(f"Generated JWT Token (valid for 24 hours):")
    print(token)

    # Also output as JSON for parsing
    print(f"\nFull token info:")
    print(json.dumps({
        "token": token,
        "user_id": "test_user",
        "expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }, indent=2))

except Exception as e:
    print(f"Error generating token: {e}", file=sys.stderr)
    sys.exit(1)
