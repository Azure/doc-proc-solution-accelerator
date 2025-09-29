targetScope = 'resourceGroup' // Resource group scope

@description('Name prefix for all resources')
param namePrefix string = 'docproc'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

// ################################################
// Application specific parameters

@description('Cosmos DB database name')
param cosmosDbName string = 'docproc'

param cosmosDBContainerNames array = [
  'pipelines'
  'service_catalog'
  'service_instances'
  'step_catalog'
  'step_instances'
  'vaults'
  'vault_documents'
  'batch_executions'
  'pipeline_executions'
]

@description('Name of the blob storage container for vault documents')
param vaultsContainerName string = 'vault-docs'

@description('Name of the storage queue for document processing requests that the worker will process')
param docprocExecutionsQueueName string = 'docproc-execution-requests'


var resourceGroupId = resourceGroup().id
var tags = {
  Environment: environment
  Project: 'doc-proc-solution-accelerator'
}

// User Assigned Identity for Container Apps to access other resources
  module userAssignedIdentity 'modules/user-assigned-identity.bicep' = {
    name: 'userAssignedIdentityDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
    params: {
      userAssignedIdentityName: toLower('${namePrefix}-uai-${uniqueString(resourceGroupId)}')
      location: location
      tags: tags
    }
  }

// Log Analytics Workspace
module logAnalytics 'modules/log-analytics-ws.bicep' = {
  name: 'logAnalyticsDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
  params: {
    logAnalyticsWorkspaceName: toLower('${namePrefix}-law-${uniqueString(resourceGroupId)}')
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    location: location
    tags: tags
  }
}

// Application Insights
module appInsights 'modules/app-insights.bicep' = {
  name: 'appInsightsDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
  params: {
    appInsightsName: toLower('${namePrefix}-appi-${uniqueString(resourceGroupId)}')
    location: location
    logAnalyticsResourceId: logAnalytics.outputs.resourceId
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    tags: tags
  }
}

// Storage Account (with Blob Container and Queue)
module storage 'modules/storage.bicep' = {
  name: 'storageAccountDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
  params: {
    storageAccountName: toLower('${namePrefix}sta${uniqueString(resourceGroupId)}')
    location: location
    vaultsContainerName: vaultsContainerName
    docprocExecutionsQueueName: docprocExecutionsQueueName
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    tags: tags
  }
}

// Cosmos DB
module cosmosDb 'modules/cosmos-db.bicep' = {
  name: 'cosmosDbDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
  params: {
    location: location
    cosmosAccountName: toLower('${namePrefix}-cosmosdb-${uniqueString(resourceGroup().id)}')
    cosmosDbName: cosmosDbName
    cosmosDBContainerNames: cosmosDBContainerNames
    cosmosDBDataContributorPrincipalIds: [userAssignedIdentity.outputs.principalId, deployer().objectId]
    zoneRedundant: environment == 'prod' ? true : false
    tags: tags
  }
}

// App Configuration Store
module appConfigStore 'modules/app-config-store.bicep' = {
  name: 'appConfigStoreDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
  params: {
    appConfigStoreName: toLower('${namePrefix}-acs-${uniqueString(resourceGroupId)}')
    location: location
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    configurationKeyValues: [
      // api app specific key vaules, uses the prefix: 'doc-proc.api.<key>'
      {
        contentType: 'text/plain'
        name: 'doc-proc.api.DEBUG'
        value: 'true'
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.api.BLOB_STORAGE_ACCOUNT_NAME'
        value: storage.outputs.name
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.api.BLOB_STORAGE_CONTAINER_NAME'
        value: 'vaults'
      }
      // worker app specific key values, uses the prefix: 'doc-proc.worker.<key>'
      {
        contentType: 'text/plain'
        name: 'doc-proc.worker.DEBUG'
        value: 'true'
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.worker.DEBUG'
        value: 'true'
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.worker.WORKER_POOL_SIZE'
        value: '2'
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.worker.WORKER_SHUTDOWN_TIMEOUT'
        value: '30'
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.worker.WORKER_AUTO_RESTART'
        value: 'true'
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.worker.WORKER_HEALTH_CHECK_INTERVAL'
        value: '10'
      }
      // shared key values, uses the prefix: 'doc-proc.<key>'
      {
        contentType: 'text/plain'
        name: 'doc-proc.COSMOS_DB_ENDPOINT'
        value: cosmosDb.outputs.cosmosEndpoint
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.COSMOS_DB_NAME'
        value: cosmosDbName
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.STORAGE_ACCOUNT_WORKER_QUEUE_URL'
        value: storage.outputs.queueUrl
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.STORAGE_WORKER_QUEUE_NAME'
        value: storage.outputs.queueName
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.APPINSIGHTS_INSTRUMENTATIONKEY'
        value: appInsights.outputs.instrumentationKey
      }
      
    ]
    tags: tags
  }
}

// Container Registry
module containerRegistry 'modules/container-registry.bicep' = {
  name: 'containerRegistryDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
  params: {
    containerRegistryName: toLower('${namePrefix}acr${uniqueString(resourceGroupId)}')
    location: location
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    tags: tags
  }
}

// Container Apps Environment (shared by all container apps)
module containerAppsEnvironment 'modules/container-apps-environment.bicep' = {
  name: 'containerAppsEnvironmentDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
  params: {
    containerAppsEnvironmentName: toLower('${namePrefix}-containerenv-${uniqueString(resourceGroupId)}')
    logAnalyticsWorkspaceId: logAnalytics.outputs.logAnalyticsWorkspaceId
    logAnalyticsPrimarySharedKey: logAnalytics.outputs.primarySharedKey
    userAssignedResourceIds: [userAssignedIdentity.outputs.resourceId]
    location: location
    tags: tags
  }
}


output userAssignedIdentityPrincipalId string = userAssignedIdentity.outputs.principalId
output userAssignedIdentityResourceId string = userAssignedIdentity.outputs.resourceId
output userAssignedIdentityClientId string = userAssignedIdentity.outputs.clientId
output containerRegistryName string = containerRegistry.outputs.name
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer
output containerAppsEnvironmentId string = containerAppsEnvironment.outputs.resourceId
output storageAccountName string = storage.outputs.name
output appConfigStoreName string = appConfigStore.outputs.name
output appConfigStoreEndpoint string = appConfigStore.outputs.endpoint
output cosmosAccountName string = cosmosDb.outputs.cosmosAccountName
