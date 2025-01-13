from azure.cosmos import CosmosClient
import os
from datetime import datetime

class CosmosOperator:
    def __init__(self):
        self.connection_string = os.environ['AzureCosmosDBConnectionString']
        self.client = CosmosClient.from_connection_string(self.connection_string)
        
    def get_container(self, database_name, container_name):
        database = self.client.get_database_client(database_name)
        return database.get_container_client(container_name)

    def get_culvana_container(self, container_name="users"):
        return self.get_container("culvana-db", container_name)

    def get_invoice_container(self):
        return self.get_container("InvoicesDB", "Invoices")
        
    def get_recipe_container(self):
        return self.get_container("InvoicesDB", "Recipes")

    def check_user_exists(self, email: str) -> bool:
        container = self.get_culvana_container("users")
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return len(items) > 0

    def get_user_by_email(self, email: str):
        container = self.get_culvana_container("users")
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return items[0] if items else None

    def get_user_invoices(self, email: str):
        container = self.get_invoice_container()
        query = "SELECT * FROM c WHERE c.userId = @email"
        parameters = [{"name": "@email", "value": email}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return items

    def get_user_recipes(self, email: str):
        container = self.get_recipe_container()
        query = "SELECT * FROM c WHERE c.id = @email"
        parameters = [{"name": "@email", "value": email}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return items