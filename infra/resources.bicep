targetScope = 'resourceGroup'


@description('Nombre del proyecto')
param projectName string

@description('Ambiente del despliegue')
param environment string

@description('Región de Azure')
param location string

@description('Correo para alertas')
param alertEmail string


var suffix = uniqueString(resourceGroup().id)

var storageAccountName = take(
  toLower('st${projectName}${environment}${suffix}'),
  24
)

var dataFactoryName = 'adf-${projectName}-${environment}-${suffix}'

var keyVaultName = take(
  toLower('kv-${projectName}-${environment}-${suffix}'),
  24
)

var logAnalyticsName = 'law-${projectName}-${environment}'

var actionGroupName = 'ag-${projectName}-${environment}'


var containers = [
  'bronze'
  'silver'
  'gold'
]


var tags = {
  project: projectName
  environment: environment
}


resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location

  sku: {
    name: 'Standard_LRS'
  }

  kind: 'StorageV2'

  properties: {
    isHnsEnabled: true
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }

  tags: tags
}


resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
}


resource storageContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for container in containers: {
    parent: blobService
    name: container

    properties: {
      publicAccess: 'None'
    }
  }
]


resource dataFactory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: dataFactoryName
  location: location

  tags: tags
}


resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location

  properties: {
    tenantId: subscription().tenantId

    sku: {
      family: 'A'
      name: 'standard'
    }

    enableRbacAuthorization: true
    softDeleteRetentionInDays: 7
  }

  tags: tags
}


resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location

  properties: {
    retentionInDays: 30

    sku: {
      name: 'PerGB2018'
    }
  }

  tags: tags
}


resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: actionGroupName
  location: 'global'

  properties: {
    groupShortName: 'retailmax'
    enabled: true

    emailReceivers: [
      {
        name: 'alert-email'
        emailAddress: alertEmail
        useCommonAlertSchema: true
      }
    ]
  }
}


output storageAccountName string = storageAccount.name
output dataFactoryName string = dataFactory.name
output keyVaultName string = keyVault.name
output logAnalyticsName string = logAnalytics.name
output actionGroupName string = actionGroup.name
