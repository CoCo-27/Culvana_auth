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
            active = req_body.get('active', "Yes")
            inventory_category = req_body.get('inventroyCategory')
            inventory_count_by = req_body.get('inventoryCountBy')
            unit_of_measure = req_body.get('unitOfMeasure', '')
            locations = req_body.get('locations', [])
            image = req_body.get('image')
            item_number = req_body.get('itemNumber')

            logging.info(f"Processing update inventory request for email: {email}")
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid request body"}),
                mimetype="application/json",
                status_code=400
            )

        if not all([email, inventory_item, item_number]):
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
            return func.HttpResponse(
                json.dumps({"error": "User document not found"}),
                mimetype="application/json",
                status_code=404
            )

        item_found = False
        current_date = datetime.utcnow().isoformat()

        for item in user_doc.get('items', []):
            if item.get('Item Number') == item_number:
                item.update({
                    "Inventory Item Name": inventory_item,
                    "Item Type": item_type,
                    "Nutritional Label": nutritional_label or "",
                    "UPC": upc or "",
                    "Active": active,
                    "Category": inventory_category,
                    "Inventory Count By": inventory_count_by,
                    "Inventory Unit of Measure": unit_of_measure,
                    "Locations": [{"name": loc.get("name", ""), "status": loc.get("status", "active")} for loc in locations],
                    "Image": image,
                    "timestamp": current_date,
                    "Item Number": item_number
                })
                item_found = True
                break

        if not item_found:
            return func.HttpResponse(
                json.dumps({"error": "Inventory item not found"}),
                mimetype="application/json",
                status_code=404
            )

        user_doc['last_updated'] = current_date

        result = container.upsert_item(body=user_doc)

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Inventory item updated successfully",
                "data": result
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error updating inventory item: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Failed to update inventory item",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        ) 