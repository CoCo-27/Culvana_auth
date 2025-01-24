import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator
from datetime import datetime

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Get request body
        try:
            req_body = req.get_json()
            print("req_body = ", req_body)
            email = req_body.get('email')
            inventory_item = req_body.get('inventoryItem')
            item_type = req_body.get('itemType')
            nutritional_label = req_body.get('nutritionalLabel')
            upc = req_body.get('upc')
            active = req_body.get('active', True)
            inventory_category = req_body.get('inventroyCategory')  # Note: Frontend typo
            inventory_count_by = req_body.get('inventoryCountBy')
            unit_of_measure = req_body.get('unitOfMeasure', '')  # Default empty string
            locations = req_body.get('locations', [])
            image = req_body.get('image')

            logging.info(f"Processing add inventory request for email: {email}")
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid request body"}),
                mimetype="application/json",
                status_code=400
            )

        # Validate required fields - removed unit_of_measure from required fields
        if not all([email, inventory_item, item_type, inventory_category, inventory_count_by]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields"}),
                mimetype="application/json",
                status_code=400
            )

        # Initialize database operator
        db = CosmosOperator()
        container = db.get_container("InvoicesDB", "Inventory")

        # Get user document
        try:
            user_doc = container.read_item(item=email, partition_key=email)
        except Exception as e:
            # If user document doesn't exist, create new one
            user_doc = {
                "id": email,
                "userId": email,
                "items": [],
                "last_updated": ""
            }

        current_date = datetime.utcnow().isoformat()
        batch_number = len(user_doc.get('items', [])) + 1

        # Create new inventory item
        new_item = {
            "Inventory Item Name": inventory_item,
            "Item Type": item_type,
            "Nutritional Label": nutritional_label or "",  # Default empty string if None
            "UPC": upc or "",  # Default empty string if None
            "Active": "No" if active is False else "Yes",  # Explicit check for False
            "Category": inventory_category,
            "Inventory Count By": inventory_count_by,
            "Inventory Unit of Measure": unit_of_measure,
            "Locations": [{"name": loc.get("name", ""), "status": loc.get("status", "active")} for loc in locations],
            "Image": image,
            "timestamp": current_date,
            "batchNumber": batch_number
        }

        # Update user document
        if 'items' not in user_doc:
            user_doc['items'] = []

        user_doc['items'].append(new_item)
        user_doc['last_updated'] = current_date

        # Save to database
        result = container.upsert_item(body=user_doc)

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Inventory item added successfully",
                "data": new_item
            }),
            mimetype="application/json",
            status_code=201
        )

    except Exception as e:
        logging.error(f"Error adding inventory item: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Failed to add inventory item",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        ) 