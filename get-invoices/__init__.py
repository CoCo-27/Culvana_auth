import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator

def format_invoice_response(invoice_data):
   return {
       'Invoice Number': invoice_data['Invoice Number'],
       'Supplier Name': invoice_data['Supplier Name'],
       'Order Date': invoice_data['Order Date'],
       'Ship Date': invoice_data['Ship Date'],
       'Total': invoice_data['Total'],
       'Items': invoice_data['Items'],
       'Shipping Address': invoice_data['Shipping Address']
   }

async def main(req: func.HttpRequest) -> func.HttpResponse:
   try:
       # Get request body
       try:
           req_body = req.get_json()
           email = req_body.get('email')
       except ValueError:
           return func.HttpResponse(
               json.dumps({"error": "Please provide an email in the request body"}),
               mimetype="application/json",
               status_code=400
           )

       if not email:
           return func.HttpResponse(
               json.dumps({"error": "Email is required"}),
               mimetype="application/json",
               status_code=400
           )

       # Initialize database operator
       db = CosmosOperator()
       container = db.get_container("InvoicesDB", "Invoices")
       
       # Query for specific user's invoices
       query = "SELECT * FROM c WHERE c.userId = @email"
       parameters = [{"name": "@email", "value": email}]
           
       items = list(container.query_items(
           query=query,
           parameters=parameters,
           enable_cross_partition_query=True
       ))
       
       if not items:
           return func.HttpResponse(
               json.dumps({
                   "status": "success", 
                   "invoices": []
               }),
               mimetype="application/json",
               status_code=200
           )
       
       # Get invoices from the user document
       invoices = []
       for item in items:
           for invoice in item['invoices']:
               invoices.append(format_invoice_response(invoice))
       
       return func.HttpResponse(
           json.dumps({
               "status": "success", 
               "invoices": invoices
           }),
           mimetype="application/json",
           status_code=200
       )
       
   except Exception as e:
       logging.error(f"Error getting invoices: {str(e)}")
       return func.HttpResponse(
           json.dumps({
               "error": "Failed to fetch invoices",
               "details": str(e)
           }),
           mimetype="application/json",
           status_code=500
       )