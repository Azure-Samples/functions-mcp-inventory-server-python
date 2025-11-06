"""
Clothing Store Inventory MCP Server

A simple, standalone FastMCP server for managing clothing store inventory.
Uses streamable HTTP transport and Azure Table Storage for persistent data.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP
from azure.data.tables import TableServiceClient, TableClient
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastMCP server
# Tell Functions host which port to listen to
# mcp_port = int(os.environ.get("FUNCTIONS_CUSTOMHANDLER_PORT", 8080))
mcp = FastMCP(
    name="clothing-inventory-server",
    stateless_http=True,
    # port=mcp_port
)

# Azure Table Storage configuration
STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME", "")
MANAGED_IDENTITY_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "")
TABLE_NAME = "ClothingInventory"
table_client: Optional[TableClient] = None

def get_table_client() -> TableClient:
    """Get or create the Table Storage client."""
    global table_client
    
    if table_client is None:
        if not STORAGE_ACCOUNT_NAME:
            raise ValueError("STORAGE_ACCOUNT_NAME environment variable not set")
        
        account_url = f"https://{STORAGE_ACCOUNT_NAME}.table.core.windows.net"
        
        # Use managed identity with explicit client ID
        from azure.identity import ManagedIdentityCredential
        if MANAGED_IDENTITY_CLIENT_ID:
            logger.info(f"Using ManagedIdentityCredential with client_id: {MANAGED_IDENTITY_CLIENT_ID[:8]}...")
            credential = ManagedIdentityCredential(client_id=MANAGED_IDENTITY_CLIENT_ID)
        else:
            logger.warning("No client ID found, using default ManagedIdentityCredential")
            credential = ManagedIdentityCredential()
        
        # Create table client directly
        table_client = TableClient(
            endpoint=account_url,
            table_name=TABLE_NAME,
            credential=credential
        )
        
        # Create table if it doesn't exist
        try:
            table_client.create_table()
            logger.info(f"Created table: {TABLE_NAME}")
        except Exception as e:
            # Table might already exist
            logger.info(f"Table {TABLE_NAME} status: {e}")
    
    return table_client

def init_inventory():
    """Initialize Table Storage with sample data if empty."""
    try:
        client = get_table_client()
        
        # Check if table has any data
        entities = list(client.list_entities(select="PartitionKey"))
        
        if len(entities) == 0:
            # Load sample data
            import importlib
            import inventory_data
            importlib.reload(inventory_data)
            from inventory_data import SAMPLE_INVENTORY
            
            # Insert sample data into Table Storage
            for item in SAMPLE_INVENTORY:
                entity = {
                    "PartitionKey": "INVENTORY",
                    "RowKey": str(item['id']),
                    "ItemId": item['id'],
                    "Name": item['name'],
                    "Category": item['category'],
                    "Price": item['price'],
                    "Description": item['description'],
                    "Sizes": json.dumps(item['sizes'])  # Store sizes as JSON string
                }
                client.upsert_entity(entity)
            
            logger.info(f"Table Storage initialized with {len(SAMPLE_INVENTORY)} items")
        else:
            logger.info(f"Table Storage already contains {len(entities)} items")
            
    except Exception as e:
        logger.error(f"Error initializing Table Storage: {e}")
        # Don't raise - allow the server to start and initialize on first request
        logger.warning("Table Storage initialization deferred")

# FastMCP Tools
@mcp.tool()
def get_inventory() -> Dict[str, Any]:
    """Get all clothing items in inventory with sizes and quantities."""
    try:
        client = get_table_client()
        entities = list(client.query_entities("PartitionKey eq 'INVENTORY'"))
        
        # If empty, try to initialize
        if len(entities) == 0:
            logger.info("No inventory found, initializing...")
            init_inventory()
            entities = list(client.query_entities("PartitionKey eq 'INVENTORY'"))
        
        items = []
        for entity in entities:
            items.append({
                'id': entity['ItemId'],
                'name': entity['Name'],
                'category': entity['Category'],
                'price': entity['Price'],
                'description': entity['Description'],
                'sizes': json.loads(entity['Sizes'])
            })
        
        return {
            "items": items,
            "total_items": len(items),
            "categories": list(set(item['category'] for item in items))
        }
    except Exception as e:
        logger.error(f"Error getting inventory: {e}")
        return {"error": str(e), "success": False}

@mcp.tool()
def add_item(
    name: str, 
    category: str, 
    price: float, 
    description: str = "", 
    sizes: Dict[str, int] = None
) -> Dict[str, Any]:
    """Add a new clothing item to inventory.
    
    Args:
        name: Name of the clothing item
        category: Category (e.g., T-Shirts, Jeans, Dresses)  
        price: Price of the item
        description: Item description (optional)
        sizes: Sizes and quantities (e.g., {"S": 10, "M": 15}) (optional)
    """
    if sizes is None:
        sizes = {"S": 0, "M": 0, "L": 0}
    
    try:
        client = get_table_client()
        
        # Get the next available ID
        entities = list(client.query_entities("PartitionKey eq 'INVENTORY'", select="ItemId"))
        next_id = max([e['ItemId'] for e in entities], default=0) + 1
        
        entity = {
            "PartitionKey": "INVENTORY",
            "RowKey": str(next_id),
            "ItemId": next_id,
            "Name": name,
            "Category": category,
            "Price": price,
            "Description": description,
            "Sizes": json.dumps(sizes)
        }
        
        client.upsert_entity(entity)
        
        new_item = {
            'id': next_id,
            'name': name,
            'category': category,
            'price': price,
            'description': description,
            'sizes': sizes
        }
        
        return {"success": True, "item": new_item}
    except Exception as e:
        logger.error(f"Error adding item: {e}")
        return {"error": str(e), "success": False}

@mcp.tool()
def get_item_by_id(item_id: int) -> Dict[str, Any]:
    """Get details of a specific item by ID.
    
    Args:
        item_id: ID of the item to retrieve
    """
    try:
        client = get_table_client()
        entity = client.get_entity(partition_key="INVENTORY", row_key=str(item_id))
        
        item = {
            'id': entity['ItemId'],
            'name': entity['Name'],
            'category': entity['Category'],
            'price': entity['Price'],
            'description': entity['Description'],
            'sizes': json.loads(entity['Sizes'])
        }
        
        return {"success": True, "item": item}
    except Exception as e:
        if "ResourceNotFound" in str(type(e).__name__):
            return {"success": False, "error": "Item not found"}
        logger.error(f"Error getting item {item_id}: {e}")
        return {"error": str(e), "success": False}

@mcp.tool()
def update_item_quantity(item_id: int, size: str, quantity: int) -> Dict[str, Any]:
    """Update stock quantity for a specific item and size.
    
    Args:
        item_id: ID of the item to update
        size: Size to update (e.g., "S", "M", "L")
        quantity: New quantity
    """
    try:
        client = get_table_client()
        entity = client.get_entity(partition_key="INVENTORY", row_key=str(item_id))
        
        # Parse sizes, update the specific size, and save back
        sizes = json.loads(entity['Sizes'])
        
        if size not in sizes:
            return {"success": False, "error": f"Size '{size}' not found for this item"}
        
        sizes[size] = quantity
        entity['Sizes'] = json.dumps(sizes)
        
        # Update the entity
        client.update_entity(entity, mode="replace")
        
        # Return the updated item
        item = {
            'id': entity['ItemId'],
            'name': entity['Name'],
            'category': entity['Category'],
            'price': entity['Price'],
            'description': entity['Description'],
            'sizes': sizes
        }
        
        return {"success": True, "item": item}
    except Exception as e:
        if "ResourceNotFound" in str(type(e).__name__):
            return {"success": False, "error": "Item not found"}
        logger.error(f"Error updating quantity: {e}")
        return {"error": str(e), "success": False}

@mcp.tool()
def search_items(query: str) -> Dict[str, Any]:
    """Search items by name or category.
    
    Args:
        query: Search query to match against item names or categories
    """
    try:
        client = get_table_client()
        entities = client.query_entities("PartitionKey eq 'INVENTORY'")
        
        query_lower = query.lower()
        results = []
        
        for entity in entities:
            if query_lower in entity['Name'].lower() or query_lower in entity['Category'].lower():
                results.append({
                    'id': entity['ItemId'],
                    'name': entity['Name'],
                    'category': entity['Category'],
                    'price': entity['Price'],
                    'description': entity['Description'],
                    'sizes': json.loads(entity['Sizes'])
                })
        
        return {
            "items": results,
            "count": len(results),
            "query": query
        }
    except Exception as e:
        logger.error(f"Error searching items: {e}")
        return {"error": str(e), "success": False}
    
def main():
    """Run the Clothing Inventory MCP Server."""
    
    try:
        
        logger.info("Starting Clothing Inventory MCP Server")
        logger.info(f"MCP Server will start on default port 8000")
        
        # Initialize Table Storage (non-blocking - errors are logged but don't stop startup)
        try:
            init_inventory()
        except Exception as e:
            logger.error(f"Table Storage initialization failed, will retry on first request: {e}")
        
        # Run the server
        logger.info("Starting MCP server with streamable-http transport")
        mcp.run(transport="streamable-http")
        
    except Exception as e:
        logger.error(f"Server crashed with error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        # Import traceback for detailed error info
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Re-raise for Azure Functions to handle
        raise

if __name__ == "__main__":
    main()