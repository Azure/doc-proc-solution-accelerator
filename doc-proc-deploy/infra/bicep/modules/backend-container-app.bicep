@description('Name prefix for resources')
param namePrefix string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Container Apps Environment resource ID')
param containerAppsEnvironmentId string

@description('Container Registry name')
param containerRegistryName string

@description('User Assigned Identity resource ID')
param userAssignedIdentityResourceId string

@description('User Assigned Identity principal ID')
param userAssignedIdentityPrincipalId string

@description('App Configuration Store endpoint')
param appConfigStoreEndpoint string

@description('CORS allowed origins')
param allowOrigins string[] = ['*']

@description('Additional environment variables')
param additionalEnvironmentVariables array = []

@description('Image tag')
param imageTag string = 'latest'

@description('Tags for resources')
param tags object = {}

var appName = '${namePrefix}-backend'
var imageName = 'doc-proc-backend'
var fullImageName = '${containerRegistryName}.azurecr.io/${imageName}:${imageTag}'

// // ACR Task to build the backend image (for manual builds)
// resource acrTask 'Microsoft.ContainerRegistry/registries/tasks@2019-06-01-preview' = if (enableAcrTask) {
//   name: '${containerRegistryName}/${appName}-build-task'
//   location: location
//   identity: {
//     type: 'UserAssigned'
//     userAssignedIdentities: {
//       '${userAssignedIdentityResourceId}': {}
//     }
//   }
//   properties: {
//     platform: {
//       os: 'Linux'
//       architecture: 'amd64'
//     }
//     agentConfiguration: {
//       cpu: 2
//     }
//     step: {
//       type: 'Docker'
//       dockerFilePath: 'doc-proc-ui/backend-app/Dockerfile'
//       contextPath: '.'
//       imageNames: [
//         'cpscontainerreg.azurecr.io/contentprocessor/latest'
//       ]
//       isPushEnabled: true
//       noCache: false
//       arguments: []
//     }
//     trigger: {
//       baseImageTrigger: {
//         baseImageTriggerType: 'Runtime'
//         name: 'defaultBaseimageTriggerName'
//       }
//     }
//   }
// }

// // Note: Initial image build should be done manually using:
// // az acr build --registry <registry-name> --image doc-proc-backend:latest ./doc-proc-ui/backend-app

// Prepare environment variables
var environmentVariables = concat([
  {
    name: 'AZURE_APP_CONFIG_ENDPOINT'
    value: appConfigStoreEndpoint
  }
  {
    name: 'AZURE_CLIENT_ID'
    value: userAssignedIdentityPrincipalId
  }
], additionalEnvironmentVariables)

// Container App for the backend
module backendApp 'br:mcr.microsoft.com/bicep/avm/res/app/container-app:0.18.1' = {
  name: 'backendAppDeployment'
  params: {
    name: appName
    location: location
    tags: tags
    environmentResourceId: containerAppsEnvironmentId
    managedIdentities: {
      userAssignedResourceIds: [userAssignedIdentityResourceId]
    }
    corsPolicy: {
      allowCredentials: true
      allowedOrigins: allowOrigins
      allowedMethods: ['*']
      allowedHeaders: ['*']
    }
    ingressAllowInsecure: false
    containers: [
      {
        name: appName
        image: 'cpscontainerreg.azurecr.io/contentprocessorapi/latest'
        resources: {
          cpu: '1.0'
          memory: '2Gi'
        }
        env: environmentVariables
        probes: [
          {
            type: 'Liveness'
            httpGet: {
              path: '/health'
              port: 8090
            }
            initialDelaySeconds: 30
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3
          }
          {
            type: 'Readiness'
            httpGet: {
              path: '/health'
              port: 8090
            }
            initialDelaySeconds: 15
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3
          }
        ]
      }
    ]
    ingressExternal: true
    ingressTargetPort: 8090
  }
}

output containerAppName string = backendApp.outputs.name
output containerAppUrl string = backendApp.outputs.fqdn
output imageName string = fullImageName
