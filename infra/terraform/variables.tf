# Variables for Azure Database for MySQL

variable "mysql_admin_username" {
  description = "MySQL administrator username"
  type        = string
  default     = "ai_team_admin"
}

variable "mysql_admin_password" {
  description = "MySQL administrator password"
  type        = string
  sensitive   = true
  default     = "AiTeam2024!Secure"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "mysql_sku" {
  description = "MySQL SKU"
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "mysql_version" {
  description = "MySQL version"
  type        = string
  default     = "8.0.21"
}

variable "storage_size_gb" {
  description = "Storage size in GB"
  type        = number
  default     = 20
}

variable "backup_retention_days" {
  description = "Backup retention days"
  type        = number
  default     = 7
}
