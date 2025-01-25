import azure.functions as func
import json
import logging
from shared_code.db_operations import CosmosOperator

def format_recipe_response(recipe):
   recipe_data = recipe['data']
   return {
       'Recipe Name': recipe_data['recipe_name'],
       'Yields': recipe_data['total_yield'],
       'Servings': recipe_data['servings'],
       'items_per_serving': recipe_data['items_per_serving'],
       'Ingredients': recipe_data['ingredients'],
       'total_cost': recipe_data['total_cost'],
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
       container = db.get_container("InvoicesDB", "Menu")
       
       query = "SELECT * FROM c WHERE c.id = @email"
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
                   "menus": []
               }),
               mimetype="application/json",
               status_code=200
           )
    
       menus = []
       for item in items:
            menu_key = f'inventory-items-{email}'
            if menu_key in item.get('recipes', {}):
                for recipe in item['recipes'][menu_key]:
                    if recipe.get('data', {}):
                        logging.info(f"Processing recipe: {recipe.get('data', {}).get('recipe_name')}")
                        menus.append(format_recipe_response(recipe))
       
       return func.HttpResponse(
           json.dumps({
               "status": "success", 
               "menus": menus
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