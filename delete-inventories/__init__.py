import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            req_body = req.get_json()
            email = req_body.get('email')
            item_number = req_body.get('item_number')
            logging.info(f"Processing delete request for email: {email}, item: {item_number}")
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Please provide email and item_number in the request body"}),
                mimetype="application/json",
                status_code=400
            )

        if not email or not item_number:
            return func.HttpResponse(
                json.dumps({"error": "Email and item_number are required"}),
                mimetype="application/json",
                status_code=400
            )

        db = CosmosOperator()
        container = db.get_container("InvoicesDB", "Inventory")
        
        try:
            # Read the specific document
            document = container.read_item(
                item=email,
                partition_key=email
            )
            
            logging.info(f"Document structure: {json.dumps(document, indent=2)}")
            
            if 'items' not in document:
                return func.HttpResponse(
                    json.dumps({
                        "error": "Invalid document structure - missing items array",
                        "document_keys": list(document.keys())
                    }),
                    mimetype="application/json",
                    status_code=500
                )
            
            original_length = len(document['items'])
            document['items'] = [
                item for item in document['items']
                if item.get('Item Number') != item_number
            ]
            
            if len(document['items']) == original_length:
                return func.HttpResponse(
                    json.dumps({"error": "Item not found in inventory"}),
                    mimetype="application/json",
                    status_code=404
                )
            
            document['itemCount'] = len(document['items'])
            
            result = container.replace_item(
                item=document['id'],
                body=document
            )
            
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "Item deleted successfully",
                    "itemCount": document['itemCount']
                }),
                mimetype="application/json",
                status_code=200
            )
            
        except Exception as e:
            logging.error(f"Database operation error: {str(e)}")
            logging.error(f"Document content (if available): {document if 'document' in locals() else 'Not available'}")
            return func.HttpResponse(
                json.dumps({"error": "Failed to perform database operation", "details": str(e)}),
                mimetype="application/json",
                status_code=500
            )
        
    except Exception as e:
        logging.error(f"Error deleting inventory item: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Failed to delete inventory item",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )