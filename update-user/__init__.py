import azure.functions as func
import logging
import json
from datetime import datetime
from shared_code.db_operations import CosmosOperator

def main(req: func.HttpRequest) -> func.HttpResponse:
   logging.info('Processing update user request.')
   
   try:
       req_body = req.get_json()
       logging.info(f"Request body: {req_body}")
       
       email = req_body.get('email')
       first_name = req_body.get('firstName')
       last_name = req_body.get('lastName')
       company_name = req_body.get('companyName')
       phone_number = req_body.get('phoneNumber')
       country = req_body.get('country')
       
       if not all([email, first_name, last_name, company_name, phone_number, country]):
           return func.HttpResponse(
               json.dumps({"error": {"message": "All fields are required"}}),
               status_code=400,
               mimetype="application/json"
           )

       db = CosmosOperator()
       
       if db.check_user_exists(email):
           container = db.get_culvana_container("users")
           user = db.get_user_by_email(email)
           
           if not user:
               return func.HttpResponse(
                   json.dumps({"error": {"message": "User not found"}}),
                   status_code=404,
                   mimetype="application/json"
               )

           user.update({
               "first_name": first_name,
               "last_name": last_name,
               "company_name": company_name,
               "phone_number": phone_number,
               "country": country,
               "updatedAt": datetime.utcnow().isoformat(),
               "profileComplete": True
           })

           container.upsert_item(user)

           return func.HttpResponse(
               json.dumps({
                   "status": "success",
                   "message": "User information updated successfully",
                   "user": {
                       "email": email,
                       "first_name": first_name,
                       "last_name": last_name,
                       "company_name": company_name,
                       "phone_number": phone_number,
                       "country": country
                   }
               }),
               status_code=200,
               mimetype="application/json"
           )
           
       return func.HttpResponse(
           json.dumps({"error": {"message": "User not found"}}),
           status_code=404,
           mimetype="application/json"
       )

   except Exception as e:
       logging.error(f"Update user error: {str(e)}")
       return func.HttpResponse(
           json.dumps({"error": {"message": f"An unexpected error occurred: {str(e)}"}}),
           status_code=500,
           mimetype="application/json"
       )