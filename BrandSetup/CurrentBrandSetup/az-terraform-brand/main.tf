resource "azurerm_resource_group" "ResourceGroup" {
  name     = "${var.Brand}ResourceGroup"
  location = "West US"
}

resource "azurerm_role_assignment" "MicrosoftGraph" {
  scope = azurerm_resource_group.ResourceGroup.id
  role_definition_name = "Contributor"
  principal_id = "2b52bc90-a523-45bb-9a14-51c129500139"
}

resource "azurerm_role_assignment" "OpenAIAppManagement" {
  scope = azurerm_resource_group.ResourceGroup.id
  role_definition_name = "Cognitive Services Language Owner"
  principal_id = "4aac6e13-a827-4e73-8b05-527380e5e1b1"
}


resource "azurerm_cognitive_account" "Authoring" {
  name                = "${var.Brand}-Authoring"
  location            = azurerm_resource_group.ResourceGroup.location
  resource_group_name = azurerm_resource_group.ResourceGroup.name
  kind                = "LUIS.Authoring"

  sku_name = "F0"

  depends_on = [
    azurerm_resource_group.ResourceGroup
  ]
}

resource "azurerm_cognitive_account" "App" {
  name                = "${var.Brand}App"
  location            = azurerm_resource_group.ResourceGroup.location
  resource_group_name = azurerm_resource_group.ResourceGroup.name
  kind                = "LUIS"

  sku_name = "S0"

  depends_on = [
    azurerm_resource_group.ResourceGroup
  ]
}

resource "azurerm_cognitive_account" "ReportingApp" {
  name                = "${var.Brand}ReportingApp"
  location            = azurerm_resource_group.ResourceGroup.location
  resource_group_name = azurerm_resource_group.ResourceGroup.name
  kind                = "LUIS"

  sku_name = "S0"

  depends_on = [
    azurerm_resource_group.ResourceGroup
  ]
}

resource "azurerm_storage_account" "storage_account" {
  name                     = var.storage_name
  resource_group_name      = azurerm_resource_group.ResourceGroup.name
  location                 = azurerm_resource_group.ResourceGroup.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  depends_on = [
    azurerm_resource_group.ResourceGroup
  ]
}

resource "azurerm_cognitive_account" "SpeechServices" {
  name                = "${var.Brand}SpeechServices"
  location            = azurerm_resource_group.ResourceGroup.location
  resource_group_name = azurerm_resource_group.ResourceGroup.name
  kind                = "SpeechServices"
  sku_name            = "S0"

}

resource "azurerm_monitor_diagnostic_setting" "diagnostic" {
  name               = var.diagnostic_setting
  target_resource_id = azurerm_cognitive_account.SpeechServices.id
  storage_account_id = azurerm_storage_account.storage_account.id

  enabled_log {
    category = "Audit"
    #enabled = true
    retention_policy {
      enabled = true
      days    = 0
    }
  }

  enabled_log {
    category = "Trace"
    retention_policy {
      enabled = true
      days    = 0
    }
  }

  metric {
    category = "AllMetrics"

    retention_policy {
      enabled = true
      days = 0
    }
  }

  depends_on = [
    azurerm_resource_group.ResourceGroup,
    azurerm_storage_account.storage_account,
    azurerm_cognitive_account.SpeechServices
  ]
}

resource "azurerm_cognitive_account" "OpenAIResource" {
  name                = "z-${var.Brand}"
  location            = "East US"
  resource_group_name = azurerm_resource_group.ResourceGroup.name
  custom_subdomain_name = "z-${var.Brand}"
  kind                = "OpenAI"
  sku_name            = "S0"
}

resource "azurerm_cognitive_account" "cognitive_account" {
  name                = "tts-${var.Brand}"
  resource_group_name = azurerm_resource_group.ResourceGroup.name
  location            = "East US"
  kind                = "CognitiveServices"
  sku_name            = "S0"

  custom_subdomain_name = "tts-${var.Brand}"
}

resource "azurerm_cognitive_deployment" "Deployment" {
  name                 = "${var.Brand}_v1"
  cognitive_account_id = azurerm_cognitive_account.OpenAIResource.id
  model {
    format  = "OpenAI"
    name    = "gpt-35-turbo"
    #version = "0301" -> deprecated by Azure
    version = "0125"
  }

  sku {
    name = "Standard"
    capacity = 120
  }
}

variable "subscription_name" {
  
}

variable "Brand" {
  # default = "tobereplaced"
}


variable "storage_name" {
  
}

variable "diagnostic_setting" {
  
}
