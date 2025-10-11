# Outputs for Azure Database for MySQL

output "mysql_server_name" {
  value       = azurerm_mysql_flexible_server.ai_team.name
  description = "MySQL server name"
}

output "mysql_server_fqdn" {
  value       = azurerm_mysql_flexible_server.ai_team.fqdn
  description = "MySQL server FQDN"
}

output "mysql_database_name" {
  value       = azurerm_mysql_flexible_database.ai_team.name
  description = "MySQL database name"
}

output "mysql_port" {
  value       = 3306
  description = "MySQL port"
}

output "connection_string" {
  value       = "mysql://${var.mysql_admin_username}:${var.mysql_admin_password}@${azurerm_mysql_flexible_server.ai_team.fqdn}:3306/${azurerm_mysql_flexible_database.ai_team.name}"
  description = "MySQL connection string"
  sensitive   = true
}

output "jdbc_connection_string" {
  value       = "jdbc:mysql://${azurerm_mysql_flexible_server.ai_team.fqdn}:3306/${azurerm_mysql_flexible_database.ai_team.name}?useSSL=true&requireSSL=true"
  description = "JDBC connection string"
}

output "resource_group_name" {
  value       = azurerm_resource_group.ai_team.name
  description = "Resource group name"
}

output "location" {
  value       = azurerm_resource_group.ai_team.location
  description = "Azure region"
}
