@description('Location for all resources')
param location string = resourceGroup().location

@description('Name prefix for worker resources')
param namePrefix string = 'docproc'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Container Apps Environment resource ID')
param containerAppsEnvironmentId string

@description('Container Registry Server')
param containerRegistryServer string

@description('Container image for the backend app')
param containerImage string

@description('CPU cores for the container')
param cpuCores string = '1.0'

@description('Memory in GB for the container')
param memoryInGB string = '2Gi'

@description('User Assigned Identity Client ID used by the api app to access resources')
param userAssignedIdentityClientId string

@description('User Assigned Identity Resource ID used as identity for the api app')
param userAssignedIdentityResourceId string

@description('App Configuration Store resource endpoint')
param appConfigStoreEndpoint string

@description('Additional environment variables')
param additionalEnvironmentVariables array = []

@description('Tags for resources')
param tags object = {}

var appName = '${namePrefix}-worker-${environment}'

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
    value: userAssignedIdentityClientId
  }
], additionalEnvironmentVariables)


// Use Azure Verified Module for Container App (Worker)
module workerApp 'br:mcr.microsoft.com/bicep/avm/res/app/container-app:0.18.1' = {
  name: 'workerAppDeployment'
  params: {
    name: appName
    location: location
    tags: tags
    environmentResourceId: containerAppsEnvironmentId
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
      userAssignedResourceIds: [ userAssignedIdentityResourceId ]
    }
    registries: [
      {
        server: containerRegistryServer
        identity: userAssignedIdentityResourceId
      }
    ]
  }
}

output containerAppName string = workerApp.outputs.name
output containerAppId string = workerApp.outputs.resourceId
