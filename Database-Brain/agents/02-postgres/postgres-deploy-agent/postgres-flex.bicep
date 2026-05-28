// =========================================================================
// postgres-flex.bicep
// Azure Database for PostgreSQL Flexible Server — Oracle migration target
// =========================================================================
// Idempotent. See instructions.md for full parameter docs.

@description('Globally unique server name (lowercase, 3-63 chars).')
param serverName string

@description('Azure region.')
param location string = resourceGroup().location

@allowed([ '13', '14', '15', '16' ])
param pgVersion string = '16'

@allowed([ 'Burstable', 'GeneralPurpose', 'MemoryOptimized' ])
param tier string = 'Burstable'

@description('SKU name (must match tier). Examples: Standard_B2ms, Standard_D4ds_v5, Standard_E4ds_v5.')
param skuName string = 'Standard_B2ms'

@minValue(32)
@maxValue(32768)
param storageSizeGb int = 128

param storageAutogrow bool = true

@description('Postgres native admin user (used by Ora2Pg / DMS).')
param adminUser string = 'pgadmin'

@description('Key Vault secret URI holding the admin password.')
@secure()
param adminPassword string

@description('Entra principal object ID granted PG admin.')
param entraAdminObjectId string

@description('UPN or app display name for the Entra admin.')
param entraAdminPrincipalName string

@allowed([ 'Public', 'Private' ])
param accessMode string = 'Public'

@description('Required when accessMode = Public. CIDR /32 for operator.')
param allowedSourceIp string = ''

@description('Required when accessMode = Private. Delegated subnet ID.')
param vnetSubnetId string = ''

@description('Required when accessMode = Private. Private DNS zone resource ID.')
param privateDnsZoneId string = ''

param enableLogicalReplication bool = true

@description('Extensions to whitelist via azure.extensions parameter.')
param enabledExtensions array = [
  'uuid-ossp'
  'pgcrypto'
  'pg_trgm'
  'orafce'
]

@allowed([ 'Disabled', 'ZoneRedundant', 'SameZone' ])
param haMode string = 'Disabled'

@minValue(7)
@maxValue(35)
param backupRetentionDays int = 7

param geoRedundantBackup bool = false

// ---------------- Server ----------------
resource pg 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: serverName
  location: location
  sku: {
    name: skuName
    tier: tier
  }
  properties: {
    version: pgVersion
    administratorLogin: adminUser
    administratorLoginPassword: adminPassword
    createMode: 'Default'
    storage: {
      storageSizeGB: storageSizeGb
      autoGrow: storageAutogrow ? 'Enabled' : 'Disabled'
    }
    backup: {
      backupRetentionDays: backupRetentionDays
      geoRedundantBackup: geoRedundantBackup ? 'Enabled' : 'Disabled'
    }
    highAvailability: {
      mode: haMode
    }
    network: accessMode == 'Private' ? {
      delegatedSubnetResourceId: vnetSubnetId
      privateDnsZoneArmResourceId: privateDnsZoneId
      publicNetworkAccess: 'Disabled'
    } : {
      publicNetworkAccess: 'Enabled'
    }
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Enabled'
      tenantId: subscription().tenantId
    }
  }
}

// ---------------- Firewall (public mode) ----------------
resource fwOperator 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = if (accessMode == 'Public' && !empty(allowedSourceIp)) {
  parent: pg
  name: 'allow-operator'
  properties: {
    startIpAddress: split(allowedSourceIp, '/')[0]
    endIpAddress: split(allowedSourceIp, '/')[0]
  }
}

// ---------------- Entra admin ----------------
resource entraAdmin 'Microsoft.DBforPostgreSQL/flexibleServers/administrators@2024-08-01' = {
  parent: pg
  name: entraAdminObjectId
  properties: {
    principalType: 'User'
    principalName: entraAdminPrincipalName
    tenantId: subscription().tenantId
  }
}

// ---------------- Server parameters ----------------
resource paramExtensions 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = {
  parent: pg
  name: 'azure.extensions'
  properties: {
    value: toUpper(join(enabledExtensions, ','))
    source: 'user-override'
  }
}

resource paramWalLevel 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = if (enableLogicalReplication) {
  parent: pg
  name: 'wal_level'
  properties: {
    value: 'logical'
    source: 'user-override'
  }
}

resource paramMaxWalSenders 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = if (enableLogicalReplication) {
  parent: pg
  name: 'max_wal_senders'
  properties: {
    value: '10'
    source: 'user-override'
  }
}

resource paramMaxReplSlots 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = if (enableLogicalReplication) {
  parent: pg
  name: 'max_replication_slots'
  properties: {
    value: '10'
    source: 'user-override'
  }
}

resource paramTls 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = {
  parent: pg
  name: 'require_secure_transport'
  properties: {
    value: 'ON'
    source: 'user-override'
  }
}

// ---------------- Outputs ----------------
output serverFqdn string = pg.properties.fullyQualifiedDomainName
output connectionString string = 'host=${pg.properties.fullyQualifiedDomainName} dbname=postgres user=${adminUser} sslmode=require'
output serverId string = pg.id
