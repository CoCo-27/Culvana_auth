import random
import hashlib
from datetime import datetime, timedelta

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def create_otp_hash(otp: str):
    """Create a hash of the OTP"""
    return hashlib.sha256(otp.encode()).hexdigest()