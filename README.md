# Model Context Protocol (MCP) Inventory Server using Azure Developer CLI

This template repository contains a Model Context Protocol (MCP) server implementation for managing clothing store inventory in Python. The sample can be easily deployed to Azure using the Azure Developer CLI (`azd`). It uses managed identity and a virtual network to make sure deployment is secure by default. You can opt out of a VNet being used in the sample by setting VNET_ENABLED to false in the parameters.

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard that enables secure connections between host applications (like Claude Desktop, IDEs, or other AI tools) and external data sources and tools. MCP allows AI assistants to securely interact with local and remote resources while maintaining user control and privacy.

This sample demonstrates how to create an MCP server that provides tools for managing clothing inventory, including adding items, searching inventory, updating quantities, and retrieving item details. The server uses FastMCP for HTTP transport and SQLite for data persistence.

## Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local?pivots=programming-language-python#install-the-azure-functions-core-tools)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- To use Visual Studio Code to run and debug locally:
  - [Visual Studio Code](https://code.visualstudio.com/)
  - [Azure Functions extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)

## Initialize the local project

You can initialize a project from this `azd` template in one of these ways:

- Use this `azd init` command from an empty local (root) folder:
  ```bash
  azd init --template functions-mcp-inventory-server-python
  ```
  Supply an environment name, such as `mcpinventory` when prompted. In `azd`, the environment is used to maintain a unique deployment context for your app.

- Clone the GitHub template repository locally using the `git clone` command:
  ```bash
  git clone https://github.com/Azure-Samples/functions-mcp-inventory-server-python.git
  cd functions-mcp-inventory-server-python
  ```
  You can also clone the repository from your own fork in GitHub.

## Prepare your local environment

1. Navigate to the app folder and create a file in that folder named `local.settings.json` that contains this JSON data:

    ```json
    {
        "IsEncrypted": false,
        "Values": {
            "FUNCTIONS_WORKER_RUNTIME": "python"
        }
    }
    ```
2. Create a Python virtual environment and activate it 

## Run your app from the terminal

1. From the app folder, install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the Functions host locally:
   ```bash
   func start
   ```

3. The MCP server will be available at `http://localhost:7071/mcp` and will accept MCP protocol requests. The server provides the following tools:
   - `add_item`: Add a new clothing item to inventory
   - `get_inventory`: Get all items with their sizes and quantities
   - `get_item_by_id`: Get details of a specific item
   - `search_items`: Search items by name or category
   - `update_item_quantity`: Update stock quantity for specific item and size

4. Connect to the MCP server by going to _mcp.json_ (inside _.vscode/_) and clicking **start** button above the local server. 

5. Test the server by opening VSCode Copilot in agent mode and asking it questions related to clothing inventory.

6. When you're done, press Ctrl+C in the terminal window to stop the app

## Run your app using Visual Studio Code

1. Open the app folder in a new terminal.
2. Run the `code .` command to open the project in Visual Studio Code.
3. Install Python dependencies by running `pip install -r requirements.txt` in the terminal.
4. Press Run/Debug (F5) to run in the debugger. Select Debug anyway if prompted about local emulator not running.
5. The MCP server will be available at `http://localhost:7071/mcp` and ready to accept MCP protocol requests.

### Data Management

The server uses SQLite for local data persistence with automatic initialization from sample data. The inventory data is stored in two tables:
- `items`: Core item information (name, category, price, description)
- `item_sizes`: Size-specific quantities for each item

### Sample Data (`inventory_data.py`)

The server includes sample clothing inventory data that's automatically loaded into the database. You can modify this file to customize the initial inventory:

```python
SAMPLE_INVENTORY = [
    {
        "id": 1,
        "name": "Navy Single-Breasted Slim Fit Formal Blazer",
        "category": "Jackets",
        "price": 89.99,
        "description": "Tailored navy blazer with notch lapels",
        "sizes": {
            "XS": 0, "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0, "XXXL": 0
        }
    },
    # More items...
]
```

## Deploy to Azure

Run this command to provision the function app, with any required Azure resources, and deploy your code:

```bash
azd up
```

By default, this sample prompts to enable a virtual network for enhanced security. If you want to deploy without a virtual network without prompting, you can configure `VNET_ENABLED` to `false` before running `azd up`:

```bash
azd env set VNET_ENABLED false
azd up
```

You're prompted to supply these required deployment parameters:

| Parameter | Description |
|-----------|-------------|
| Environment name | An environment that's used to maintain a unique deployment context for your app. You won't be prompted if you created the local project using azd init. |
| Azure subscription | Subscription in which your resources are created. |
| Azure location | Azure region in which to create the resource group that contains the new Azure resources. Only regions that currently support the Flex Consumption plan are shown. |

## Test deployed app

Once deployment is done, test the MCP server by making requests to the deployed endpoint. To get the endpoint quickly, run the following:

```bash
az functionapp function list --resource-group <resource-group-name> --name <function-app-name> --query "[].{name:name, url:invokeUrlTemplate}" --output table
```

The MCP server endpoint should look like:

```
https://<function-app-name>.azurewebsites.net/mcp
```

## Server authentication
Sample server currently has anonymous access, which is not secured. Will add authentication layer soon!

## Redeploy your code

You can run the `azd up` command as many times as you need to both provision your Azure resources and deploy code updates to your function app.

> **Note**: Deployed code files are always overwritten by the latest deployment package.

## Clean up resources

When you're done working with your function app and related resources, you can use this command to delete the function app and its related resources from Azure and avoid incurring any further costs:

```bash
azd down
```

## About

This repository contains an MCP (Model Context Protocol) server implementation for clothing inventory management written in Python. It's deployed to Azure Functions Flex Consumption plan using the Azure Developer CLI (azd). The sample uses managed identity and a virtual network to make sure deployment is secure by default.

The MCP server provides tools for:
- Adding new clothing items with sizes and quantities
- Searching and retrieving inventory items
- Updating stock quantities
- Managing clothing store inventory through the MCP protocol

This enables AI assistants and other MCP-compatible applications to securely interact with inventory data while maintaining proper access controls and data persistence.