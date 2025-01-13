import azure.functions as func
import logging
import json
from shared_code.email_service import EmailService
from shared_code.db_operations import CosmosOperator
from shared_code.otp_utils import generate_otp, create_otp_hash
from datetime import datetime, timedelta

def main(req: func.HttpRequest) -> func.HttpResponse:
   logging.info('Processing resend OTP request.')
   
   try:
       req_body = req.get_json()
       email = req_body.get('email')
       
       if not email:
           return func.HttpResponse(
               json.dumps({"error": {"message": "Email is required"}}),
               status_code=400,
               mimetype="application/json"
           )

       # Initialize database operator
       db = CosmosOperator()
       
       # Check if there's a pending registration
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

       # Generate new OTP
       otp = generate_otp()
       otp_hash = create_otp_hash(otp)
       expiry_time = datetime.utcnow() + timedelta(minutes=10)

       # Update registration with new OTP
       registration.update({
           "otpHash": otp_hash,
           "expiresAt": expiry_time.isoformat(),
           "attempts": 0  # Reset attempts counter
       })
       
       temp_container.upsert_item(registration)

       # Send new OTP
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
               "message": "New verification code sent successfully",
               "email": email
           }),
           status_code=200,
           mimetype="application/json"
       )

   except Exception as e:
       logging.error(f"Resend OTP error: {str(e)}")
       return func.HttpResponse(
           json.dumps({"error": {"message": "An unexpected error occurred"}}),
           status_code=500,
           mimetype="application/json"
       )