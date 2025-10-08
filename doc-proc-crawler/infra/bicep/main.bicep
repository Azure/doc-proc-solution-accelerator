@description('Name prefix for worker resources')
param namePrefix string = 'docproc'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Container Apps Environment resource name where the container apps will be deployed')
param containerAppsEnvironment string

@description('Container Registry Server')
param containerRegistryServer string

@description('Container image for the backend app')
param containerImage string

@description('CPU cores for the container')
param cpuCores string = '1.0'

@description('Memory in GB for the container')
param memoryInGB string = '2Gi'

@description('User Assigned Identity Resource Name used as identity for the api app')
param userAssignedIdentityName string

@description('App Configuration Store resource endpoint')
param appConfigStoreEndpoint string

@description('Additional environment variables')
param additionalEnvironmentVariables array = []

@description('Tags for resources')
param tags object = {}

var appName = '${namePrefix}-crawler-${environment}'

// Prepare environment variables
var environmentVariables = concat([
  {
    name: 'AZURE_APP_CONFIG_CONNECTION_STRING'
    value: ''
  }
  {
    name: 'AZURE_APP_CONFIG_ENDPOINT'
    value: appConfigStoreEndpoint
  }
  {
    name: 'AZURE_CLIENT_ID'
    value: userAssignedIdentity.properties.clientId
  }
], additionalEnvironmentVariables)


// Fetch existing User Assigned Identity
resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  scope: resourceGroup()
  name: userAssignedIdentityName
}

resource containerAppsEnvironmentResource 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironment
  scope: resourceGroup()
}

// Use Azure Verified Module for Container App (Crawler)
module crawlerApp 'br:mcr.microsoft.com/bicep/avm/res/app/container-app:0.18.1' = {
  name: 'crawlerAppDeployment'
  params: {
    name: appName
    location: resourceGroup().location
    tags: tags
    environmentResourceId: containerAppsEnvironmentResource.id
    ingressAllowInsecure: false
    disableIngress: true
    containers: [
      {
        name: appName
        image: containerImage
        resources: {
          cpu: cpuCores
          memory: memoryInGB
        }
        env: environmentVariables
      }
    ]
    // Worker doesn't need external ingress
    ingressExternal: false
    managedIdentities: {
      systemAssigned: false
      userAssignedResourceIds: [ userAssignedIdentity.id ]
    }
    registries: [
      {
        server: containerRegistryServer
        identity: userAssignedIdentity.id
      }
    ]
  }
}

output containerAppName string = crawlerApp.outputs.name
output containerAppId string = crawlerApp.outputs.resourceId
