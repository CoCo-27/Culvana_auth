import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator

def format_invoice_response(invoice_data):
    """Format the invoice response with complete structure"""
    return {
        "Supplier Name": invoice_data.get('Supplier Name', ''),
        "Sold to Address": invoice_data.get('Sold to Address', ''),
        "Order Date": invoice_data.get('Order Date', ''),
        "Ship Date": invoice_data.get('Ship Date', ''),
        "Invoice Number": invoice_data.get('Invoice Number', ''),
        "Shipping Address": invoice_data.get('Shipping Address', ''),
        "Total": invoice_data.get('Total', 0),
        "PO_NUMBER": invoice_data.get('PO_NUMBER', ''),
        "location": invoice_data.get('location', ''),
        "status": invoice_data.get('status', ''),
        "Items": [format_invoice_item(item) for item in invoice_data.get('Items', [])]
    }

def format_invoice_item(item):
    """Format individual invoice items with complete structure"""
    return {
        "Item Number": item.get('Item Number', ''),
        "Item Name": item.get('Item Name', ''),
        "Product Category": item.get('Product Category', ''),
        "Quantity In a Case": item.get('Quantity In a Case', 0),
        "Measurement Of Each Item": item.get('Measurement Of Each Item', 0),
        "Measured In": item.get('Measured In', ''),
        "Quantity Shipped": item.get('Quantity Shipped', 0),
        "Extended Price": item.get('Extended Price', 0),
        "Total Units Ordered": item.get('Total Units Ordered', 0),
        "Case Price": item.get('Case Price', 0),
        "Catch Weight": item.get('Catch Weight', 'N/A'),
        "Priced By": item.get('Priced By', 'per each'),
        "Splitable": item.get('Splitable', 'NO'),
        "Split Price": item.get('Split Price', 'N/A'),
        "Cost of a Unit": item.get('Cost of a Unit', 0),
        "Cost of Each Item": item.get('Cost of Each Item', 0),
        "Currency": item.get('Currency', 'USD'),
        "page_number": item.get('page_number', 1),
        "item_index": item.get('item_index', 0)
    }

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            req_body = req.get_json()
            email = req_body.get('email')
            print("email = ", email)
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
        container = db.get_container("InvoicesDB", "Invoices")
        
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
                    "data": {
                        "id": email,
                        "userId": email,
                        "invoices": []
                    }
                }),
                mimetype="application/json",
                status_code=200
            )
        
        user_doc = items[0]
        formatted_response = {
            "id": user_doc.get('id', email),
            "userId": user_doc.get('userId', email),
            "invoices": [format_invoice_response(invoice) for invoice in user_doc.get('invoices', [])]
        }
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "data": formatted_response
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