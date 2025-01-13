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
   }

async def main(req: func.HttpRequest) -> func.HttpResponse:
   try:
       # Get request body
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

       # Initialize database operator
       db = CosmosOperator()
       container = db.get_container("InvoicesDB", "Recipes")
       
       # Query for specific user's recipes
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
                   "recipes": []
               }),
               mimetype="application/json",
               status_code=200
           )
       
       # Get recipes from the user document
       recipes = []
       for item in items:
           recipe_key = f'inventory-items-{email}'
           if recipe_key in item.get('recipes', {}):
               for recipe in item['recipes'][recipe_key]:
                   logging.info(f"Processing recipe: {recipe.get('data', {}).get('recipe_name')}")
                   recipes.append(format_recipe_response(recipe))
       
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