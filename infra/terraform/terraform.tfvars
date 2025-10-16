# Copy this file to terraform.tfvars and update the values

# MySQL Configuration
mysql_admin_username = "ai_team_admin"
mysql_admin_password = "AiTeam2024!SecureMySQL"

# Environment
environment = "production"
location    = "West US 2"

# MySQL Server Configuration
mysql_sku           = "GP_Standard_D2ds_v4"
mysql_version       = "8.0.21"
storage_size_gb     = 20
backup_retention_days = 7
