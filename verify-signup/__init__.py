import azure.functions as func
import logging
import json
import jwt
import os
from datetime import datetime, timedelta
from shared_code.db_operations import CosmosOperator
from shared_code.otp_utils import create_otp_hash

# Use the same JWT configuration as login
JWT_SECRET = os.environ['JWT_SECRET']
REGULAR_TOKEN_EXPIRY = timedelta(hours=24)

def generate_token(user_id):
   expiry = datetime.utcnow() + REGULAR_TOKEN_EXPIRY
   return jwt.encode({
       'user_id': user_id,
       'exp': expiry,
       'iat': datetime.utcnow()
   }, JWT_SECRET, algorithm='HS256')

def main(req: func.HttpRequest) -> func.HttpResponse:
   logging.info('Processing signup verification.')
   
   try:
       req_body = req.get_json()
       email = req_body.get('email')
       otp = req_body.get('otp')
       
       if not email or not otp:
           return func.HttpResponse(
               json.dumps({"error": {"message": "Email and OTP are required"}}),
               status_code=400,
               mimetype="application/json"
           )

       # Initialize database operator
       db = CosmosOperator()

       # Get pending registration
       temp_container = db.get_culvana_container("temp_registrations")
       query = "SELECT * FROM c WHERE c.email = @email"
       parameters = [{"name": "@email", "value": email}]
       
       items = list(temp_container.query_items(
           query=query,
           parameters=parameters,
           enable_cross_partition_query=True
       ))
       
       if not items:
           return func.HttpResponse(
               json.dumps({"error": {"message": "No pending registration found"}}),
               status_code=404,
               mimetype="application/json"
           )

       registration = items[0]
       
       # Check expiry
       if datetime.utcnow() > datetime.fromisoformat(registration['expiresAt']):
           return func.HttpResponse(
               json.dumps({"error": {"message": "Verification code has expired"}}),
               status_code=400,
               mimetype="application/json"
           )

       # Verify OTP
       if create_otp_hash(otp) != registration['otpHash']:
           registration['attempts'] += 1
           temp_container.upsert_item(registration)
           
           if registration['attempts'] >= 3:
               return func.HttpResponse(
                   json.dumps({"error": {"message": "Too many failed attempts"}}),
                   status_code=400,
                   mimetype="application/json"
               )
           
           return func.HttpResponse(
               json.dumps({"error": {"message": "Invalid verification code"}}),
               status_code=400,
               mimetype="application/json"
           )

       # Create verified user
       users_container = db.get_culvana_container("users")
       new_user = {
           "id": email,
           "email": email,
           "passwordHash": registration['passwordHash'],
           "createdAt": datetime.utcnow().isoformat(),
           "verified": True,
           "status": "active",
           "profileComplete": False
       }
       
       users_container.create_item(new_user)
       
       # Delete temporary registration
       temp_container.delete_item(registration['id'], partition_key=registration['id'])

       # Generate token using the same method as login
       token = generate_token(new_user['id'])

       return func.HttpResponse(
           json.dumps({
               "status": "success",
               "message": "Email verified successfully",
               "token": token,
               "user": {
                   "email": new_user['email'],
                   "verified": new_user['verified']
               }
           }),
           status_code=200,
           mimetype="application/json"
       )

   except Exception as e:
       logging.error(f"Verification error: {str(e)}")
       return func.HttpResponse(
           json.dumps({"error": {"message": "An unexpected error occurred"}}),
           status_code=500,
           mimetype="application/json"
       )