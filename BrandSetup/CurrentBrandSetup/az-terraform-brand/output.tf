output "resource_group_name" {
  value = {
    name = azurerm_resource_group.ResourceGroup.name
  }
}


output "cognitive_account_info" {
  value = {
    authoring = {
      name         = azurerm_cognitive_account.Authoring.name
      resource_key = nonsensitive(azurerm_cognitive_account.Authoring.primary_access_key)
    }
    app = {
      name         = azurerm_cognitive_account.App.name
      resource_key = nonsensitive(azurerm_cognitive_account.App.primary_access_key)
    }
    reporting_app = {
      name         = azurerm_cognitive_account.ReportingApp.name
      resource_key = nonsensitive(azurerm_cognitive_account.ReportingApp.primary_access_key)
    }
    speech_services = {
      name         = azurerm_cognitive_account.SpeechServices.name
      resource_key = nonsensitive(azurerm_cognitive_account.SpeechServices.primary_access_key)
    }
   
    openai_resource = {
      name         = azurerm_cognitive_account.OpenAIResource.name
      resource_key = nonsensitive(azurerm_cognitive_account.OpenAIResource.primary_access_key)
      endpoint     = azurerm_cognitive_account.OpenAIResource.endpoint
    }  

    cognitive_resource = {
      name         = azurerm_cognitive_account.cognitive_account.name
      resource_key = nonsensitive(azurerm_cognitive_account.cognitive_account.primary_access_key)
      endpoint     = azurerm_cognitive_account.cognitive_account.endpoint
    }

  }
}

output "speech_services_info" {
  value = {
    resource_key = nonsensitive(azurerm_cognitive_account.SpeechServices.primary_access_key)
    endpoint     = azurerm_cognitive_account.SpeechServices.endpoint
  }
}

output "cognitive_deployment_info" {
  value = {
    name = azurerm_cognitive_deployment.Deployment.name
  }
}
