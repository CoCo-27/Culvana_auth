import azure.functions as func
import logging
import json
from datetime import datetime, timedelta
from shared_code.db_operations import CosmosOperator
from shared_code.email_service import EmailService
import bcrypt
import random
import hashlib

def generate_otp():
   """Generate a 6-digit OTP"""
   return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def create_otp_hash(otp: str):
   """Create a hash of the OTP"""
   return hashlib.sha256(otp.encode()).hexdigest()

def main(req: func.HttpRequest) -> func.HttpResponse:
   logging.info('Processing signup request.')
   
   try:
       req_body = req.get_json()
       email = req_body.get('email')
       password = req_body.get('password')
       
       if not email or not password:
           return func.HttpResponse(
               json.dumps({"error": {"message": "Email and password are required"}}),
               status_code=400,
               mimetype="application/json"
           )

       if len(password) < 8:
           return func.HttpResponse(
               json.dumps({"error": {"message": "Password must be at least 8 characters long"}}),
               status_code=400,
               mimetype="application/json"
           )

       db = CosmosOperator()
       
       if db.check_user_exists(email):
           return func.HttpResponse(
               json.dumps({"error": {"message": "Email already registered"}}),
               status_code=409,
               mimetype="application/json"
           )

       salt = bcrypt.gensalt()
       hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

       otp = generate_otp()
       otp_hash = create_otp_hash(otp)
       expiry_time = datetime.utcnow() + timedelta(minutes=10)

       temp_container = db.get_culvana_container("temp_registrations")
       temp_registration = {
           "id": email,
           "email": email,
           "passwordHash": hashed_password.decode('utf-8'),
           "otpHash": otp_hash,
           "expiresAt": expiry_time.isoformat(),
           "attempts": 0,
           "status": "pending"
       }
       
       temp_container.upsert_item(temp_registration)

       email_service = EmailService()
       if not email_service.send_otp_email(email, otp):
           return func.HttpResponse(
               json.dumps({"error": {"message": "Failed to send verification code"}}),
               status_code=500,
               mimetype="application/json"
           )

       return func.HttpResponse(
           json.dumps({
               "status": "success",
               "message": "Verification code sent successfully",
               "email": email
           }),
           status_code=200,
           mimetype="application/json"
       )

   except Exception as e:
       logging.error(f"Signup error: {str(e)}")
       return func.HttpResponse(
           json.dumps({"error": {"message": f"An unexpected error occurred: {str(e)}"}}),
           status_code=500,
           mimetype="application/json"
       )