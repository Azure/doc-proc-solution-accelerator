targetScope = 'resourceGroup'

import * as const from 'constants/constants.bicep'

param environmentName string
param location string = resourceGroup().location
param label string = 'gpt-rag'

@description('Principal ID for role assignments. This is typically the Object ID of the user or service principal running the deployment.')
param principalId string

@description('Principal type for role assignments. This can be "User", "ServicePrincipal", or "Group".')
param principalType string = 'User'

@description('Tags to apply to all resources in the deployment')
param deploymentTags object = {}

param useUAI bool = true

var _containerDummyImageName string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
var resourceToken string = toLower(uniqueString(subscription().id, environmentName, location))

//get existing app config
resource appconfig 'Microsoft.AppConfiguration/configurationStores@2024-06-15-preview' existing = {
  name: '${const.abbrs.configuration.appConfiguration}${resourceToken}'
  
}

var appKeys = [
  {
    key: 'DATA_INGEST_APP_APIKEY'
    value: resourceToken
    contentType: 'text/plain'
  }
  {
    key: 'AI_FOUNDRY_ACCOUNT_CREDENTIAL_TYPE'
    value: 'default_azure_credential'
    contentType: 'text/plain'
  }
  {
    key: 'SEARCH_SERVICE_CREDENTIAL_TYPE'
    value: 'default_azure_credential'
    contentType: 'text/plain'
  }
  {
    key: 'STORAGE_ACCOUNT_CREDENTIAL_TYPE'
    value: 'default_azure_credential'
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_TENANT_ID'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_CLIENT_ID'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_SITE_DOMAIN'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_SITE_NAME'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_SUB_SITE_NAME'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_DRIVE_NAME'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_SUBFOLDERS_REGEX'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_SUBFOLDERS_NAMES'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_CLIENT_SECRET_NAME'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'AZURE_SEARCH_SHAREPOINT_INDEX_NAME'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_FILES_FORMAT'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'SHAREPOINT_FILES_TO_IGNORE'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'DEBUG'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_ENDPOINT'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_NAME'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_CONTAINER_PIPELINES'
    value: 'pipelines'
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_CONTAINER_STEP_CATALOG'
    value: 'step_catalog'
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_CONTAINER_STEP_INSTANCES'
    value: 'step_instances'
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_CONTAINER_SERVICE_CATALOG'
    value: 'service_catalog'
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_CONTAINER_SERVICE_INSTANCES'
    value: 'service_instances'
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_CONTAINER_BATCH_EXECUTIONS'
    value: 'batch_executions'
    contentType: 'text/plain'
  }
  {
    key: 'COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS'
    value: 'pipeline_executions'
    contentType: 'text/plain'
  }
  {
    key: 'STORAGE_ACCOUNT_WORKER_QUEUE_URL'
    value: ''
    contentType: 'text/plain'
  }
  {
    key: 'STORAGE_WORKER_QUEUE_NAME'
    value: 'docproc-execution-requests'
    contentType: 'text/plain'
  }
  {
    key: 'WORKER_POOL_SIZE'
    value: '0'
    contentType: 'text/plain'
  }
  {
    key: 'WORKER_AUTO_RESTART'
    value: 'True'
    contentType: 'text/plain'
  }
  {
    key: 'WORKER_SHUTDOWN_TIMEOUT'
    value: '30'
    contentType: 'text/plain'
  }
  {
    key: 'WORKER_HEALTH_CHECK_INTERVAL'
    value: '10'
    contentType: 'text/plain'
  }
]

//add app config key
resource appconfigKey 'Microsoft.AppConfiguration/configurationStores/keyValues@2024-06-15-preview' = [for key in appKeys: {
  name: '${appconfig.name}/${key.key}'
  properties: {
    value: key.value
    contentType: key.contentType
    tags: {
      label: label
    }
  }
}
]

//add cosmos db account
resource cosmosDBAccount 'Microsoft.DocumentDB/databaseAccounts@2025-05-01-preview' existing = {
  name: '${const.abbrs.databases.cosmosDBDatabase}${resourceToken}'
}

//get the cosmos database
resource cosmosDBDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-05-01-preview' existing = {
  name: '${const.abbrs.databases.cosmosDBDatabase}db${resourceToken}'
  parent: cosmosDBAccount
}

//add cosmos container - doc-proc
resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-05-01-preview' = {
  name: 'doc-proc'
  parent: cosmosDBDatabase
  properties: {
    resource: {
      id: 'doc-proc'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
    }
  }
}

//get the azure container apps service
resource containerEnv 'Microsoft.App/managedEnvironments@2025-02-02-preview' existing = {
  name: '${const.abbrs.containers.containerAppsEnvironment}${resourceToken}'
}


//DataIngest ACA User Managed Identity
module dataIngestAcaUAI 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.0' = {
  name: '${const.abbrs.security.managedIdentity}${const.abbrs.containers.containerApp}${resourceToken}-dataingest'
  params: {
    // Required parameters
    name: '${const.abbrs.security.managedIdentity}${const.abbrs.containers.containerApp}${resourceToken}-dataingest'
    // Non-required parameters
    location: location
  }
}

//DataIngest ACA User Managed Identity
module dataIngestUIAcaUAI 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.0' = {
  name: '${const.abbrs.security.managedIdentity}${const.abbrs.containers.containerApp}${resourceToken}-dataingest-ui'
  params: {
    // Required parameters
    name: '${const.abbrs.security.managedIdentity}${const.abbrs.containers.containerApp}${resourceToken}-dataingest-ui'
    // Non-required parameters
    location: location
  }
}

module containerApps 'br/public:avm/res/app/container-app:0.17.0' = {
  name: '${const.abbrs.containers.containerApp}${resourceToken}-dataingest'
  params: {
    name: '${const.abbrs.containers.containerApp}${resourceToken}-dataingest'
    location:              location
    environmentResourceId: containerEnv.id

    ingressExternal:       true
    ingressTargetPort:     80
    ingressTransport:      'auto'
    ingressAllowInsecure:  false

    dapr: {
      enabled:     true
      appId:       'dataingest'
      appPort:     80
      appProtocol: 'http'
    }

    managedIdentities: {
      systemAssigned: (useUAI) ? false : true
      userAssignedResourceIds: (useUAI) ? [dataIngestAcaUAI.outputs.resourceId] : []
    }

    scaleSettings: {
      minReplicas: 1
      maxReplicas: 1
    }
    
    containers: [
      {
        name:     'dataingest'
        image:    _containerDummyImageName
        resources: {
          cpu:    '0.5'
          memory: '1.0Gi'
        }
        env: [
          {
            name:  'APP_CONFIG_ENDPOINT'
            value: 'https://${appconfig.name}.azconfig.io'
          }
          {
            name:  'AZURE_TENANT_ID'
            value: subscription().tenantId
          }
          {
            name:  'AZURE_CLIENT_ID'
            value: useUAI ? dataIngestAcaUAI.outputs.clientId : ''
          }
        ]
      }
    ]

    tags: {
      'azd-service-name': 'dataingest'
    }
  }
}

module containerAppUI 'br/public:avm/res/app/container-app:0.17.0' = {
  name: '${const.abbrs.containers.containerApp}${resourceToken}-dataingest-ui'
  params: {
    name: '${const.abbrs.containers.containerApp}${resourceToken}-dataingest-ui'
    location:              location
    environmentResourceId: containerEnv.id

    ingressExternal:       true
    ingressTargetPort:     80
    ingressTransport:      'auto'
    ingressAllowInsecure:  false

    dapr: {
      enabled:     true
      appId:       'dataingest-ui'
      appPort:     80
      appProtocol: 'http'
    }

    managedIdentities: {
      systemAssigned: (useUAI) ? false : true
      userAssignedResourceIds: (useUAI) ? [dataIngestAcaUAI.outputs.resourceId] : []
    }

    scaleSettings: {
      minReplicas: 1
      maxReplicas: 1
    }
    
    containers: [
      {
        name:     'dataingest-ui'
        image:    _containerDummyImageName
        resources: {
          cpu:    '0.5'
          memory: '1.0Gi'
        }
        env: [
          {
            name:  'APP_CONFIG_ENDPOINT'
            value: 'https://${appconfig.name}.azconfig.io'
          }
          {
            name:  'AZURE_TENANT_ID'
            value: subscription().tenantId
          }
          {
            name:  'AZURE_CLIENT_ID'
            value: useUAI ? dataIngestAcaUAI.outputs.clientId : ''
          }
        ]
      }
    ]

    tags: {
      'azd-service-name': 'dataingest-ui'
    }
  }
}

// Cosmos DB Account - Cosmos DB Built-in Data Contributor -> Data Ingest
module assignCosmosDBCosmosDbBuiltInDataContributorExecutor 'modules/security/cosmos-data-plane-role-assignment.bicep' = {
  name: 'assignCosmosDBCosmosDbBuiltInDataContributorExecutor'
  params: {
    #disable-next-line BCP318
    cosmosDbAccountName: cosmosDBAccount.name
    principalId: useUAI ? dataIngestAcaUAI.outputs.clientId : containerApps.outputs.systemAssignedMIPrincipalId
    roleDefinitionGuid: const.roles.CosmosDBBuiltInDataContributor.guid
    scopePath: '/subscriptions/${subscription().subscriptionId}/resourceGroups/${resourceGroup().name}/providers/Microsoft.DocumentDB/databaseAccounts/${const.abbrs.databases.cosmosDBDatabase}${resourceToken}/dbs/${const.abbrs.databases.cosmosDBDatabase}db${resourceToken}'
  }
}

// Cosmos DB Account - Cosmos DB Built-in Data Contributor -> Data Ingest
module assignCosmosDBCosmosDbBuiltInDataContributorDataIngestUI 'modules/security/cosmos-data-plane-role-assignment.bicep' = {
  name: 'assignCosmosDBCosmosDbBuiltInDataContributorDataIngestUI'
  params: {
    #disable-next-line BCP318
    cosmosDbAccountName: cosmosDBAccount.name
    principalId: useUAI ? dataIngestUIAcaUAI.outputs.clientId : containerAppUI.outputs.systemAssignedMIPrincipalId
    roleDefinitionGuid: const.roles.CosmosDBBuiltInDataContributor.guid
    scopePath: '/subscriptions/${subscription().subscriptionId}/resourceGroups/${resourceGroup().name}/providers/Microsoft.DocumentDB/databaseAccounts/${const.abbrs.databases.cosmosDBDatabase}${resourceToken}/dbs/${const.abbrs.databases.cosmosDBDatabase}db${resourceToken}'
  }
}
