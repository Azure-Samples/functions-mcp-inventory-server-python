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


### Sample Data 

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
## Deployment 

1. This sample uses Visual Studio Code as the main client. Configure it as an allowed client application:
    ```shell
    azd env set PRE_AUTHORIZED_CLIENT_IDS aebc6443-996d-45c2-90f0-388ff96faa56
    ```

1. Specify a service management reference if required by your organization. If you're not a Microsoft employee and don't know that you need to set this, you can skip this step. However, if provisioning fails with an error about a missing service management reference, you may need to revisit this step. Microsoft employees using a Microsoft tenant must provide a service management reference (your Service Tree ID). Without this, you won't be able to create the Entra app registration, and provisioning will fail.
    ```shell
    azd env set SERVICE_MANAGEMENT_REFERENCE <service-management-reference>
    ```

1. Run `azd up` in the root directory. 

    You're prompted to supply these required deployment parameters:

    | Parameter | Description |
    |-----------|-------------|
    | Environment name | An environment that's used to maintain a unique deployment context for your app. You won't be prompted if you created the local project using azd init. |
    | Azure subscription | Subscription in which your resources are created. |
    | Azure location | Azure region in which to create the resource group that contains the new Azure resources. Only regions that currently support the Flex Consumption plan are shown. |

    When the deployment finishes, your terminal will display output similar to the following:

    ```shell
      (✓) Done: Resource group: rg-resource-group-name (12.061s)
      (✓) Done: App Service plan: plan-random-guid (6.748s)
      (✓) Done: Virtual Network: vnet-random-guid (8.566s)
      (✓) Done: Log Analytics workspace: log-random-guid (29.422s)
      (✓) Done: Storage account: strandomguid (34.527s)
      (✓) Done: Application Insights: appi-random-guid (8.625s)
      (✓) Done: Function App: func-mcp-random-guid (36.096s)
      (✓) Done: Private Endpoint: blob-private-endpoint (30.67s)

      Deploying services (azd deploy)
      (✓) Done: Deploying service api
      - Endpoint: https://functionapp-name.azurewebsites.net/
    ```

### Redeploy your code

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