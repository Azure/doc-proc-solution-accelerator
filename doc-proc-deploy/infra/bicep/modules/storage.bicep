@description('Optional: Location for all resources')
param location string = resourceGroup().location

@description('Required: Storage account name')
param storageAccountName string

@description('Managed Identity that will be given access to the Storage Account')
param roleAssignedManagedIdentityPrincipalIds string[]

@description('Optional: Name of the blob container for vault documents. Default is "vaults"')
param vaultsContainerName string = 'vaults'

@description('Optional: Name of the queue for document processing requests that the worker will process. Default is "docproc-execution-requests"')
param docprocExecutionsQueueName string = 'docproc-execution-requests'

@description('Optional: Tags for resources')
param tags object = {}

var accountRoleAssignments array = [for principalId in roleAssignedManagedIdentityPrincipalIds: {
          principalId: principalId
          principalType: 'ServicePrincipal'
          roleDefinitionIdOrName: 'Contributor'        
        }
      ]

var queueRoleAssignments array = [for principalId in roleAssignedManagedIdentityPrincipalIds: {
          principalId: principalId
          principalType: 'ServicePrincipal'
          roleDefinitionIdOrName: 'Storage Queue Data Contributor'        
        }
      ]

var blobRoleAssignments array = [for principalId in roleAssignedManagedIdentityPrincipalIds: {
          principalId: principalId
          principalType: 'ServicePrincipal'
          roleDefinitionIdOrName: 'Storage Blob Data Contributor'        
        }
      ]

var deployerRoleAssignments = [
    {
      principalId: deployer().objectId
      principalType: 'User'
      roleDefinitionIdOrName: 'Storage Blob Data Contributor'        
    }
    {
      principalId: deployer().objectId
      principalType: 'User'
      roleDefinitionIdOrName: 'Storage Queue Data Contributor'        
    }
  ]

// Use Azure Verified Module for Storage Account
module storageAccount 'br/public:avm/res/storage/storage-account:0.27.0' = {
  params: {
    // Required parameters
    name: storageAccountName
    // Non-required parameters
    location: location
    kind: 'StorageV2'
    skuName: 'Standard_LRS'
    accessTier: 'Hot'
    allowSharedKeyAccess: false
    enableHierarchicalNamespace: false
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    blobServices: {
      automaticSnapshotPolicyEnabled: true
      containerDeleteRetentionPolicyDays: 7
      containerDeleteRetentionPolicyEnabled: true
      containers: [
        {
          name: vaultsContainerName
          publicAccess: 'None'
        }
      ]
    }
    queueServices: {
      queues: [
        {
          metadata: {}
          name: docprocExecutionsQueueName
        }
      ]
    }
    roleAssignments: concat(
      accountRoleAssignments,
      queueRoleAssignments,
      blobRoleAssignments,
      deployerRoleAssignments
    )
    tags: tags
  }
}

output name string = storageAccount.outputs.name
output resourceId string = storageAccount.outputs.resourceId
output queueUrl string = 'https://${storageAccount.outputs.name}.queue.${environment().suffixes.storage}/'
output queueName string = docprocExecutionsQueueName
