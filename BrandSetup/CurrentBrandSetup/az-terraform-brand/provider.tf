terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "4.23.0"
    }
  }
}

# data "azurerm_subscription" "sb" {
#   name = var.subscription_name
# }

# This is the "Default" provider
provider "azurerm" {
  # subscription_id = var.dev_sub_id
  subscription_id = var.subscription_name
  # tenant_id       = var.prod_tenant_id
  # client_id       = var.dev_client_id
  # client_secret   = var.dev_client_secret

  features {}
}

# This provider uses the "prod" alias
# provider "azurerm" {
#   alias = "prod"

#   subscription_id = var.prod_sub_id
#   tenant_id       = var.prod_tenant_id
#   client_id       = var.prod_client_id
#   client_secret   = var.prod_client_secret

#   features {}
# }
