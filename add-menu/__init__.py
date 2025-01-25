import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator
from datetime import datetime

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            req_body = req.get_json()
            email = req_body.get('email')
            item_name = req_body.get('itemName')
            recipes = req_body.get('recipes', [])
            category = req_body.get('category')
            size = req_body.get('size')
            menu_price = req_body.get('menuPrice')
            method = req_body.get('method', '')

            logging.info(f"Processing add menu request for email: {email}")
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid request body"}),
                mimetype="application/json",
                status_code=400
            )

        if not all([email, item_name, category, size, menu_price]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields"}),
                mimetype="application/json",
                status_code=400
            )

        db = CosmosOperator()
        container = db.get_menu_container()

        try:
            user_doc = container.read_item(item=email, partition_key=email)
        except Exception as e:
            user_doc = {
                "id": email,
                "type": "user",
                "recipe_count": 0,
                "recipes": {},
                "last_updated": ""
            }

        recipe_count = user_doc.get('recipe_count', 0) + 1
        recipe_id = f"{email}_inventory-items-{email}_{recipe_count}"
        current_date = datetime.utcnow().isoformat()

        new_recipe = {
            "id": recipe_id,
            "sequence_number": recipe_count,
            "name": item_name,
            "created_at": current_date,
            "data": {
                "recipe_name": item_name,
                "servings": 0,
                "items_per_serving": 1,
                "serving_size": None,
                "total_yield": None,
                "ingredients": [],
                "total_cost": 0,
                "cost_per_serving": 0,
                "Type": "Menu",
                "Size_Name": size,
                "category": category,
                "Menu_Price": menu_price,
                "Total_cost_percentage": 0,
                "Gross_Profit": 0,
                "Gross_Profit_percentage": 0,
                "method": method
            }
        }

        recipe_key = f"inventory-items-{email}"
        if recipe_key not in user_doc.get('recipes', {}):
            user_doc['recipes'][recipe_key] = []

        user_doc['recipes'][recipe_key].append(new_recipe)
        user_doc['recipe_count'] = recipe_count
        user_doc['last_updated'] = current_date

        result = container.upsert_item(body=user_doc)

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Menu item added successfully",
                "data": new_recipe
            }),
            mimetype="application/json",
            status_code=201
        )

    except Exception as e:
        logging.error(f"Error adding menu item: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Failed to add menu item",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )