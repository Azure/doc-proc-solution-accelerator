param location string
@minLength(4)
param namePrefix string = 'docproc'
param containerImage string
param cosmosDbName string = 'docproc'
param allowOrigins string = '*'

@description('Container App environment name')
var caeName = '${namePrefix}-cae'
var appName = '${namePrefix}-backend'
var logAnalyticsName = '${namePrefix}-la'
var cosmosAccountName = toLower('${namePrefix}${uniqueString(resourceGroup().id)}')

// Log Analytics
resource la 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Container Apps Environment
resource caEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: caeName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: la.properties.customerId
        sharedKey: la.listKeys().primarySharedKey
      }
    }
  }
}

// Cosmos DB account + SQL database + containers
resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  name: cosmosDbName
  parent: cosmos
  properties: {
    resource: {
      id: cosmosDbName
    }
    options: {}
  }
}

var containers = [ 'services', 'steps', 'pipelines' ]

resource sqlContainers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = [for c in containers: {
  name: c
  parent: db
  properties: {
    resource: {
      id: c
      partitionKey: {
        paths: [ '/id' ]
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: []
      }
    }
    options: {}
  }
}]

// Get connection string (primary key)
var cosmosConn = cosmos.listKeys().primaryMasterKey
var cosmosEndpoint = cosmos.properties.documentEndpoint

// Container App
resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: caEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
      secrets: [
        {
          name: 'cosmos-key'
          value: cosmosConn
        }
      ]
      activeRevisionsMode: 'Single'
      registries: []
    }
    template: {
      containers: [
        {
          name: appName
          image: containerImage
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          env: [
            {
              name: 'COSMOS_ENDPOINT'
              value: cosmosEndpoint
            }
            {
              name: 'COSMOS_KEY'
              secretRef: 'cosmos-key'
            }
            {
              name: 'COSMOS_DB_NAME'
              value: cosmosDbName
            }
            {
              name: 'ALLOW_ORIGINS'
              value: allowOrigins
            }
          ]
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 15
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

output containerAppName string = app.name
output cosmosAccount string = cosmos.name
output cosmosEndpointOut string = cosmosEndpoint
