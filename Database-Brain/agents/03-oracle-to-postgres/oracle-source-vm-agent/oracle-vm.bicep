// =========================================================================
// oracle-vm.bicep
// Oracle 21c XE on Azure VM (Oracle Linux 8) — source for Ora2Pg / DMS demo
// =========================================================================
// Idempotent: re-running az deployment group create updates without recreate.
// See instructions.md for full deployment workflow.

@description('VM name and Linux hostname. Becomes listener service name.')
param vmName string = 'vm-oracle-src'

@description('Azure region. Any region with Standard_D4s_v5 + Premium SSD.')
param location string = resourceGroup().location

@description('Linux admin username (sudo-enabled).')
param adminUsername string = 'oracleadmin'

@description('SSH public key (full OpenSSH format including type prefix).')
@secure()
param sshPublicKey string

@description('CIDR allowed for SSH and Oracle 1521. Use /32 for single operator IP.')
param allowedSourceIp string

@description('VM size. Default D4s_v5 = 4 vCPU / 16 GB.')
param vmSize string = 'Standard_D4s_v5'

@description('Data disk size for Oracle data files.')
param dataDiskSizeGb int = 128

@description('Existing Key Vault holding secret oracle-sys-password.')
param keyVaultName string

@description('Run sample schemas load (HR / SH / OE) after Oracle install.')
param loadSampleSchemas bool = true

// ---------------- Naming ----------------
var vnetName = '${vmName}-vnet'
var subnetName = 'oracle'
var nsgName = '${vmName}-nsg'
var pipName = '${vmName}-pip'
var nicName = '${vmName}-nic'
var dnsLabel = toLower(vmName)

// ---------------- Network ----------------
resource nsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgName
  location: location
  properties: {
    securityRules: [
      {
        name: 'allow-ssh'
        properties: {
          priority: 1000
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourceAddressPrefix: allowedSourceIp
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '22'
        }
      }
      {
        name: 'allow-oracle-listener'
        properties: {
          priority: 1010
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourceAddressPrefix: allowedSourceIp
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '1521'
        }
      }
    ]
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: { addressPrefixes: [ '10.50.0.0/16' ] }
    subnets: [
      {
        name: subnetName
        properties: {
          addressPrefix: '10.50.1.0/24'
          networkSecurityGroup: { id: nsg.id }
        }
      }
    ]
  }
}

resource pip 'Microsoft.Network/publicIPAddresses@2023-11-01' = {
  name: pipName
  location: location
  sku: { name: 'Standard' }
  properties: {
    publicIPAllocationMethod: 'Static'
    dnsSettings: { domainNameLabel: dnsLabel }
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2023-11-01' = {
  name: nicName
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          privateIPAllocationMethod: 'Dynamic'
          subnet: { id: '${vnet.id}/subnets/${subnetName}' }
          publicIPAddress: { id: pip.id }
        }
      }
    ]
  }
}

// ---------------- Key Vault password fetch ----------------
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Cloud-init reads Oracle SYS password from Instance Metadata Service via managed identity.
// We pass keyVaultName + secretName via custom data; the install script fetches at runtime.
var cloudInit = base64(replace(replace(loadTextContent('cloud-init.yaml'),
  '__KV_NAME__', keyVaultName),
  '__LOAD_SAMPLES__', loadSampleSchemas ? 'true' : 'false'))

// ---------------- VM ----------------
resource vm 'Microsoft.Compute/virtualMachines@2024-03-01' = {
  name: vmName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    hardwareProfile: { vmSize: vmSize }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      customData: cloudInit
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: sshPublicKey
            }
          ]
        }
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'Oracle'
        offer: 'Oracle-Linux'
        sku: 'ol88-lvm-gen2'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: { storageAccountType: 'Premium_LRS' }
      }
      dataDisks: [
        {
          lun: 0
          createOption: 'Empty'
          diskSizeGB: dataDiskSizeGb
          managedDisk: { storageAccountType: 'Premium_LRS' }
        }
      ]
    }
    networkProfile: {
      networkInterfaces: [ { id: nic.id } ]
    }
  }
}

// ---------------- RBAC: VM identity reads KV secret ----------------
// Key Vault Secrets User role
var kvSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: kv
  name: guid(kv.id, vm.id, kvSecretsUserRoleId)
  properties: {
    principalId: vm.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserRoleId)
  }
}

// ---------------- Outputs ----------------
output vmFqdn string = pip.properties.dnsSettings.fqdn
output oracleConnectionString string = '${pip.properties.dnsSettings.fqdn}:1521/XEPDB1'
output sysUserSecretRef string = '${kv.properties.vaultUri}secrets/oracle-sys-password'
output vmPrincipalId string = vm.identity.principalId
