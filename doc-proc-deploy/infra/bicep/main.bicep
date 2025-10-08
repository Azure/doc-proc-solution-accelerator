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
  {name: 'pipelines', partitionKey: '/id'}
  {name: 'service_catalog', partitionKey: '/id'}
  {name: 'service_instances', partitionKey: '/id'}
  {name: 'step_catalog', partitionKey: '/id'}
  {name: 'step_instances', partitionKey: '/id'}
  {name: 'source_catalog', partitionKey: '/id'}
  {name: 'source_instances', partitionKey: '/id'}
  {name: 'vaults', partitionKey: '/id'}
  {name: 'vault_documents', partitionKey: '/id'}
  {name: 'batch_executions', partitionKey: '/id'}
  {name: 'pipeline_executions', partitionKey: '/id'}
  {name: 'crawl_leases', partitionKey: '/source_instance_id'}
  {name: 'crawl_executions', partitionKey: '/id'}
]

@description('Name of the blob storage container for vault documents')
param vaultsContainerName string = 'vaults'

@description('Name of the storage queue for document processing requests that the worker will process')
param docprocExecutionsQueueName string = 'docproc-execution-requests'

@description('Location for AI Foundry resources')
param aiFoundryLocation string = resourceGroup().location


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
    storageAccountName: length('${namePrefix}sta${uniqueString(resourceGroupId)}') > 24 ? substring(toLower('${namePrefix}sta${uniqueString(resourceGroupId)}'), 0, 24) : toLower('${namePrefix}sta${uniqueString(resourceGroupId)}')
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
      // Crawler Worker specific key values, uses the prefix: 'doc-proc.crawler.<key>'
      {
        contentType: 'text/plain'
        name: 'doc-proc.crawler.DEBUG'
        value: 'true'
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.crawler.CRAWLER_MAX_WORKERS'
        value: '3'
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.crawler.CRAWLER_DISCOVERY_POLL_INTERVAL'
        value: '60' // in seconds
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.crawler.CRAWLER_LEASE_DURATION_MINUTES'
        value: '30' // in minutes
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.crawler.CRAWLER_LEASE_RENEWAL_INTERVAL_MINUTES'
        value: '15' // in minutes
      }
      // shared key values, uses the prefix: 'doc-proc.<key>'
      {
        contentType: 'text/plain'
        name: 'doc-proc.common.COSMOS_DB_ENDPOINT'
        value: cosmosDb.outputs.cosmosEndpoint
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.common.COSMOS_DB_NAME'
        value: cosmosDbName
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.common.STORAGE_ACCOUNT_WORKER_QUEUE_URL'
        value: storage.outputs.queueUrl
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.common.STORAGE_WORKER_QUEUE_NAME'
        value: storage.outputs.queueName
      }
      {
        contentType: 'text/plain'
        name: 'doc-proc.common.APPINSIGHTS_INSTRUMENTATIONKEY'
        value: appInsights.outputs.instrumentationKey
      }
      {
        contentType: 'text/plain'
        name: 'sentinel'
        value: '1'
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


module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'aiFoundryDeployment.${substring(uniqueString(resourceGroup().id, deployment().name), 0, 8)}'
  params: {
    aiFoundryBaseName: toLower(length('docprocai${environment}') > 12 ? substring('docprocai${environment}', 0, 12) : 'docprocai${environment}')
    roleAssignedManagedIdentityPrincipalIds: [userAssignedIdentity.outputs.principalId]
    location: aiFoundryLocation
    tags: tags
  }
}

output userAssignedIdentityName string = userAssignedIdentity.outputs.name
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
output aiProjectName string = aiFoundry.outputs.aiProjectName
output aiServicesName string = aiFoundry.outputs.aiServicesName
