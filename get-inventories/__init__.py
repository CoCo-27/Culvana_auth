import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator

def format_inventory_response(item):
    """Format invoice item for frontend inventory display"""
    return {
        "Supplier Name": item.get("Supplier Name", ""),
        "Inventory Item Name": item.get("Inventory Item Name", ""),
        "Inventory Unit of Measure": item.get("Inventory Unit of Measure", ""),
        "Brand": item.get("Brand", ""),
        "Item Name": item.get("Item Name", ""),
        "Item Number": item.get("Item Number", ""),
        "Quantity In a Case": item.get("Quantity In a Case", ""),
        "Measurement Of Each Item": item.get("Measurement Of Each Item", ""),
        "Measured In": item.get("Measured In", ""),
        "Total Units": item.get("Total Units", ""),
        "Case Price": item.get("Case Price", ""),
        "Catch Weight": item.get("Catch Weight", ""),
        "Priced By": item.get("Priced By", ""),
        "Splitable": item.get("Splitable", ""),
        "Split Price": item.get("Split Price", ""),
        "Cost of a Unit": item.get("Cost of a Unit", ""),
        "Category": item.get("Category", ""),
        "timestamp": item.get("timestamp", ""),
        "batchNumber": item.get("batchNumber", "")
    }

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            req_body = req.get_json()
            email = req_body.get('email')
            logging.info(f"Processing inventory request for email: {email}")
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

        db = CosmosOperator()
        container = db.get_container("InvoicesDB", "Inventory")
        
        query = "SELECT * FROM c WHERE c.id = @emailParam"
        parameters = [{"name": "@emailParam", "value": email}]
        
        logging.info(f"Executing query: {query} with parameters: {parameters}")
            
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        logging.info(f"Found {len(items)} items in database")
        
        if not items:
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "inventory": [],
                    "supplier_name": None,
                    "timestamp": None,
                    "itemCount": 0
                }),
                mimetype="application/json",
                status_code=200
            )

        # Get the first document (should only be one per user)
        doc = items[0]
        
        # Get items directly from the document
        if not doc.get('items'):
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "inventory": [],
                    "supplier_name": None,
                    "timestamp": None,
                    "itemCount": 0
                }),
                mimetype="application/json",
                status_code=200
            )

        # Format all items
        formatted_items = [
            format_inventory_response(item)
            for item in doc.get('items', [])
        ]
        
        response_data = {
            "status": "success",
            "inventory": formatted_items,
            "supplier_name": doc.get('supplier_name'),
            "timestamp": doc.get('timestamp'),
            "itemCount": len(formatted_items)
        }
        
        logging.info(f"Returning response with {len(formatted_items)} items")
        
        return func.HttpResponse(
            json.dumps(response_data),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error getting inventory: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Failed to fetch inventory",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )