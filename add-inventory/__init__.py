import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator
from datetime import datetime

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            req_body = req.get_json()
            print("req_body = ", req_body)
            email = req_body.get('email')
            inventory_item = req_body.get('inventoryItem')
            item_type = req_body.get('itemType')
            nutritional_label = req_body.get('nutritionalLabel')
            upc = req_body.get('upc')
            active = req_body.get('active', True)
            inventory_category = req_body.get('inventroyCategory')
            inventory_count_by = req_body.get('inventoryCountBy')
            unit_of_measure = req_body.get('unitOfMeasure', '')
            locations = req_body.get('locations', [])
            image = req_body.get('image')

            logging.info(f"Processing add inventory request for email: {email}")
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid request body"}),
                mimetype="application/json",
                status_code=400
            )

        if not all([email, inventory_item, item_type, inventory_category, inventory_count_by]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields"}),
                mimetype="application/json",
                status_code=400
            )

        db = CosmosOperator()
        container = db.get_container("InvoicesDB", "Inventory")

        try:
            user_doc = container.read_item(item=email, partition_key=email)
        except Exception as e:
            user_doc = {
                "id": email,
                "userId": email,
                "items": [],
                "last_updated": ""
            }

        current_date = datetime.utcnow().isoformat()
        batch_number = len(user_doc.get('items', [])) + 1

        new_item = {
            "Inventory Item Name": inventory_item,
            "Item Type": item_type,
            "Nutritional Label": nutritional_label or "",
            "UPC": upc or "",
            "Active": "No" if active is False else "Yes",
            "Category": inventory_category,
            "Inventory Count By": inventory_count_by,
            "Inventory Unit of Measure": unit_of_measure,
            "Locations": [{"name": loc.get("name", ""), "status": loc.get("status", "active")} for loc in locations],
            "Image": image,
            "timestamp": current_date,
            "batchNumber": batch_number
        }

        if 'items' not in user_doc:
            user_doc['items'] = []

        user_doc['items'].append(new_item)
        user_doc['last_updated'] = current_date

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