targetScope = 'subscription'


@description('Nombre del proyecto')
param projectName string

@description('Ambiente del despliegue')
@allowed([
  'dev'
  'prod'
])
param environment string

@description('Región de Azure')
param location string

@description('Correo para alertas')
param alertEmail string


var resourceGroupName = 'rg-${projectName}-${environment}'


resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: resourceGroupName
  location: location

  tags: {
    project: projectName
    environment: environment
  }
}


module resources './resources.bicep' = {
  name: 'resources-${environment}'
  scope: resourceGroup

  params: {
    projectName: projectName
    environment: environment
    location: location
    alertEmail: alertEmail
  }
}


output resourceGroupName string = resourceGroup.name
output storageAccountName string = resources.outputs.storageAccountName
output dataFactoryName string = resources.outputs.dataFactoryName
output keyVaultName string = resources.outputs.keyVaultName
