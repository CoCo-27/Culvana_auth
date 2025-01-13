import azure.functions as func
import logging
import os
import json
import bcrypt
import jwt
from datetime import datetime, timedelta
from shared_code.db_operations import CosmosOperator

JWT_SECRET = os.environ['JWT_SECRET']
REGULAR_TOKEN_EXPIRY = timedelta(hours=24)
REMEMBER_ME_EXPIRY = timedelta(days=30)

def generate_token(user_id, remember_me=False):
   expiry = datetime.utcnow() + (REMEMBER_ME_EXPIRY if remember_me else REGULAR_TOKEN_EXPIRY)
   return jwt.encode({
       'user_id': user_id,
       'exp': expiry,
       'iat': datetime.utcnow()
   }, JWT_SECRET, algorithm='HS256')

def main(req: func.HttpRequest) -> func.HttpResponse:
   logging.info('Processing login request.')
   
   try:
       req_body = req.get_json()
       email = req_body.get('email')
       password = req_body.get('password')
       remember_me = req_body.get('remember_me', False)
       
       if not email or not password:
           return func.HttpResponse(
               json.dumps({"error": {"message": "Email and password are required"}}),
               status_code=400,
               mimetype="application/json"
           )

       # Initialize database operator
       db = CosmosOperator()
       user = db.get_user_by_email(email)

       if not user:
           return func.HttpResponse(
               json.dumps({"error": {"message": "Invalid email or password"}}),
               status_code=401,
               mimetype="application/json"
           )

       # Verify password
       stored_password = user.get('passwordHash')
       if not stored_password or not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
           return func.HttpResponse(
               json.dumps({"error": {"message": "Invalid email or password"}}),
               status_code=401,
               mimetype="application/json"
           )

       # Generate token
       token = generate_token(user['id'], remember_me)

       # Update last login
       user['lastLogin'] = datetime.utcnow().isoformat()
       container = db.get_culvana_container("users")
       container.upsert_item(user)

       return func.HttpResponse(
           json.dumps({
               "status": "success",
               "message": "Login successful",
               "token": token,
               "user": {
                   "email": user['email'],
                   "verified": user['verified']
               }
           }),
           status_code=200,
           mimetype="application/json"
       )
   except Exception as e:
       logging.error(f"Login error: {str(e)}")
       return func.HttpResponse(
           json.dumps({"error": {"message": "An unexpected error occurred"}}),
           status_code=500,
           mimetype="application/json"
       )