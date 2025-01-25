import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator

def get_inventory_item(container, email, ingredient_name):
    query = """
    SELECT * FROM c 
    WHERE c.id = @email 
    AND ARRAY_LENGTH(c.items) > 0
    """
    parameters = [{"name": "@email", "value": email}]
    
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    
    if items:
        inventory_items = items[0].get('items', [])
        for item in inventory_items:
            if item.get('Inventory Item Name', '').lower() == ingredient_name.lower():
                return {
                    'Supplier Name': item.get('Supplier Name'),
                    'Inventory Unit of Measure': item.get('Inventory Unit of Measure'),
                    'Item Name': item.get('Item Name'),
                    'Item Number': item.get('Item Number'),
                    'Inventory Item Name': item.get('Inventory Item Name'),
                    'Quantity In a Case': item.get('Quantity In a Case'),
                    'Measurement Of Each Item': item.get('Measurement Of Each Item'),
                    'Measured In': item.get('Measured In'),
                    'Priced By': item.get('Priced By'),
                    'Location': item.get('Location')
                }
    return None

def format_recipe_response(recipe, inventory_container, email):
    recipe_data = recipe['data']
    total_recipe_cost = 0
    
    enhanced_ingredients = []
    for ingredient in recipe_data['ingredients']:
        inventory_item = get_inventory_item(inventory_container, email, ingredient.get('ingredient', ''))

        ingredient_cost = ingredient.get('total_cost', 0)
        total_recipe_cost += ingredient_cost

        enhanced_ingredient = {
            **ingredient,
            'inventory_data': inventory_item if inventory_item else None
        }
        
        enhanced_ingredients.append(enhanced_ingredient)
    print("enhanced_ingredients ==== ", enhanced_ingredients)
    return {
        'Recipe Name': recipe_data['recipe_name'],
        'Yields': recipe_data['total_yield'],
        'Servings': recipe_data['servings'],
        'items_per_serving': recipe_data['items_per_serving'],
        'Ingredients': enhanced_ingredients,
        'total_recipe_cost': total_recipe_cost,
    }

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            req_body = req.get_json()
            email = req_body.get('email')
            logging.info(f"Processing recipes request for email: {email}")
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
        recipes_container = db.get_container("InvoicesDB", "Recipes")
        inventory_container = db.get_container("InvoicesDB", "Inventory")
        
        query = "SELECT * FROM c WHERE c.id = @email"
        parameters = [{"name": "@email", "value": email}]
            
        items = list(recipes_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "recipes": []
                }),
                mimetype="application/json",
                status_code=200
            )
        
        recipes = []
        for item in items:
            recipe_key = f'inventory-items-{email}'
            if recipe_key in item.get('recipes', {}):
                for recipe in item['recipes'][recipe_key]:
                    if recipe.get('data', {}).get('Type') == "Recipe":
                        logging.info(f"Processing recipe: {recipe.get('data', {}).get('recipe_name')}")
                        recipes.append(format_recipe_response(recipe, inventory_container, email))
                        
        return func.HttpResponse(
            json.dumps({
                "status": "success", 
                "recipes": recipes
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error getting recipes: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Failed to fetch recipes",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )