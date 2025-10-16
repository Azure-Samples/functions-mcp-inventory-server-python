"""
Clothing Store Inventory MCP Server

A simple, standalone FastMCP server for managing clothing store inventory.
Uses streamable HTTP transport and is designed to be stateless for remote hosting.
"""

import sqlite3
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastMCP server
# Tell Functions host which port to listen to
mcp_port = int(os.environ.get("FUNCTIONS_CUSTOMHANDLER_PORT", 8080))
mcp = FastMCP(
    name="clothing-inventory-server",
    stateless_http=True,
    port=mcp_port
)

def get_db_path() -> str:
    # Get the path to the database file
    return str(Path(__file__).parent / "inventory.db")

def get_inventory_data_path() -> str:
    # Get the path to the inventory data file.
    return str(Path(__file__).parent / "inventory_data.py")

def init_database():
    # Initialize database with sample data if it doesn't exist.
    db_path = get_db_path()
    inventory_data_path = get_inventory_data_path()
    needs_reload = False
    
    # Check if inventory_data.py was modified after the database was created
    if Path(db_path).exists() and Path(inventory_data_path).exists():
        db_mtime = os.path.getmtime(db_path)
        inventory_mtime = os.path.getmtime(inventory_data_path)
        
        if inventory_mtime > db_mtime:
            print(f"inventory_data.py was updated (modified at {inventory_mtime} vs DB at {db_mtime})")
            print("Reloading database with fresh data")
            needs_reload = True
            
    import importlib
    import inventory_data
    importlib.reload(inventory_data)
    from inventory_data import SAMPLE_INVENTORY
    data_to_use = SAMPLE_INVENTORY
    
    # Initialize database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
        # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_sizes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            size TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id)
        )
    ''')
    
    # Clear existing data if the inventory file is newer or if DB is empty
    cursor.execute('SELECT COUNT(*) FROM items')
    if needs_reload or cursor.fetchone()[0] == 0:
        # Clear existing data if needed
        cursor.execute('DELETE FROM item_sizes')
        cursor.execute('DELETE FROM items')
        
        # Insert sample data
        for item in data_to_use:
            cursor.execute('''
                INSERT INTO items (id, name, category, price, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (item['id'], item['name'], item['category'], item['price'], item['description']))
            
            for size, quantity in item['sizes'].items():
                cursor.execute('''
                    INSERT INTO item_sizes (item_id, size, quantity)
                    VALUES (?, ?, ?)
                ''', (item['id'], size, quantity))
                
        print(f"Database reinitialized with {len(data_to_use)} items")
    else:
        print("Database already contains data, no reload needed")
    
    conn.commit()
    conn.close()

# FastMCP Tools
@mcp.tool()
def get_inventory() -> Dict[str, Any]:
    """Get all clothing items in inventory with sizes and quantities."""

    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.id, i.name, i.category, i.price, i.description
            FROM items i
            ORDER BY i.category, i.name
        ''')
        items = cursor.fetchall()
        
        result = []
        for item in items:
            item_id, name, category, price, description = item
            
            # Get sizes and quantities
            cursor.execute('''
                SELECT size, quantity
                FROM item_sizes
                WHERE item_id = ?
            ''', (item_id,))
            sizes_data = cursor.fetchall()
            sizes = {size: quantity for size, quantity in sizes_data}
            
            result.append({
                'id': item_id,
                'name': name,
                'category': category,
                'price': price,
                'description': description,
                'sizes': sizes
            })
        
        return {
            "items": result,
            "total_items": len(result),
            "categories": list(set(item['category'] for item in result))
        }
    except Exception as e:
        logger.error(f"Error getting inventory: {e}")
        return {"error": str(e), "success": False}
    finally:
        if conn:
            conn.close()

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
    
    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO items (name, category, price, description)
            VALUES (?, ?, ?, ?)
        ''', (name, category, price, description))
        
        item_id = cursor.lastrowid
        
        for size, quantity in sizes.items():
            cursor.execute('''
                INSERT INTO item_sizes (item_id, size, quantity)
                VALUES (?, ?, ?)
            ''', (item_id, size, quantity))
        
        conn.commit()
        
        item_response = get_item_by_id(item_id)
        
        return {"success": True, "item": item_response["item"]}
    except Exception as e:
        logger.error(f"Error adding item: {e}")
        return {"error": str(e), "success": False}
    finally:
        if conn:
            conn.close()

@mcp.tool()
def get_item_by_id(item_id: int) -> Dict[str, Any]:
    """Get details of a specific item by ID.
    
    Args:
        item_id: ID of the item to retrieve
    """
   
    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.id, i.name, i.category, i.price, i.description
            FROM items i
            WHERE i.id = ?
        ''', (item_id,))
        item = cursor.fetchone()
        
        if not item:
            return {"success": False, "error": "Item not found"}
        
        item_id, name, category, price, description = item
        
        # Get sizes and quantities
        cursor.execute('''
            SELECT size, quantity
            FROM item_sizes
            WHERE item_id = ?
        ''', (item_id,))
        sizes_data = cursor.fetchall()
        sizes = {size: quantity for size, quantity in sizes_data}
        
        result = {
            'id': item_id,
            'name': name,
            'category': category,
            'price': price,
            'description': description,
            'sizes': sizes
        }
        
        return {"success": True, "item": result}
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {e}")
        return {"error": str(e), "success": False}
    finally:
        if conn:
            conn.close()

@mcp.tool()
def update_item_quantity(item_id: int, size: str, quantity: int) -> Dict[str, Any]:
    """Update stock quantity for a specific item and size.
    
    Args:
        item_id: ID of the item to update
        size: Size to update (e.g., "S", "M", "L")
        quantity: New quantity
    """
   
    db_path = get_db_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE item_sizes
            SET quantity = ?
            WHERE item_id = ? AND size = ?
        ''', (quantity, item_id, size))
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        if affected_rows > 0:
            item_response = get_item_by_id(item_id)
            return {"success": True, "item": item_response["item"]}
        else:
            return {"success": False, "error": "Item or size not found"}
    except Exception as e:
        logger.error(f"Error updating quantity: {e}")
        return {"error": str(e), "success": False}
    finally:
        if conn:
            conn.close()

@mcp.tool()
def search_items(query: str) -> Dict[str, Any]:
    """Search items by name or category.
    
    Args:
        query: Search query to match against item names or categories
    """
   
    all_items_response = get_inventory()
    all_items = all_items_response["items"]  # Extract the items list from the response
    query = query.lower()
    
    results = [
        item for item in all_items
        if query in item['name'].lower() or query in item['category'].lower()
    ]
    
    return {
        "items": results,
        "count": len(results),
        "query": query
    }
    
def main():
    """Run the Clothing Inventory MCP Server."""
    
    try:
        
        logger.info("Starting Clothing Inventory MCP Server")
        logger.info(f"MCP Server will start on port {mcp_port}")
        
        # Initialize database
        try:
            init_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            logger.error(f"Database error type: {type(e).__name__}")
            raise
        
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