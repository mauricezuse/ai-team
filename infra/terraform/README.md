# Azure Database for MySQL - Terraform Configuration

This Terraform configuration creates an Azure Database for MySQL Flexible Server for the AI Team project.

## Prerequisites

1. **Azure CLI** installed and configured
2. **Terraform** installed (version >= 1.0)
3. **Azure subscription** with appropriate permissions

## Setup Instructions

### 1. Configure Azure CLI

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "Your-Subscription-ID"
```

### 2. Configure Terraform Variables

```bash
# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit the variables file with your values
nano terraform.tfvars
```

**Important**: Update the `mysql_admin_password` with a strong password!

### 3. Initialize and Deploy

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

### 4. Get Connection Information

After deployment, get the connection details:

```bash
# Get the connection string
terraform output connection_string

# Get the server FQDN
terraform output mysql_server_fqdn

# Get the database name
terraform output mysql_database_name
```

## Configuration Details

### MySQL Server Configuration

- **Server Type**: Azure Database for MySQL Flexible Server
- **Version**: MySQL 8.0.21
- **SKU**: GP_Standard_D2s_v3 (2 vCores, 8 GB RAM)
- **Storage**: 20 GB with auto-grow enabled
- **High Availability**: Same Zone
- **Backup**: 7 days retention

### Network Configuration

- **Virtual Network**: 10.0.0.0/16
- **MySQL Subnet**: 10.0.1.0/24
- **Firewall Rules**: 
  - Allow Azure Services
  - Allow All (for development)

### Security

- **SSL**: Required
- **Authentication**: MySQL native authentication
- **Network**: Private endpoint (recommended for production)

## Environment Variables

After deployment, update your application with these environment variables:

```bash
# Database Configuration
DATABASE_URL=mysql://username:password@server.mysql.database.azure.com:3306/ai_team
MYSQL_HOST=server.mysql.database.azure.com
MYSQL_PORT=3306
MYSQL_DATABASE=ai_team
MYSQL_USERNAME=ai_team_admin
MYSQL_PASSWORD=your_password
MYSQL_SSL_REQUIRED=true
```

## Application Updates

### 1. Update Database Configuration

Update `crewai_app/database.py`:

```python
# Change from SQLite to MySQL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://username:password@host:port/database"
```

### 2. Install MySQL Driver

```bash
pip install PyMySQL
```

### 3. Update Requirements

Add to `requirements.txt`:

```
PyMySQL>=1.0.2
```

## Production Considerations

### 1. Security

- **Private Endpoints**: Use private endpoints for production
- **Firewall Rules**: Restrict access to specific IP ranges
- **SSL/TLS**: Always use encrypted connections
- **Password Rotation**: Implement regular password rotation

### 2. Monitoring

- **Azure Monitor**: Enable monitoring and alerting
- **Performance Metrics**: Monitor CPU, memory, and storage
- **Connection Monitoring**: Track connection counts and performance

### 3. Backup and Recovery

- **Automated Backups**: 7-day retention (configurable)
- **Point-in-Time Recovery**: Available for up to 35 days
- **Cross-Region Backup**: Consider for disaster recovery

### 4. Scaling

- **Vertical Scaling**: Increase SKU for more resources
- **Read Replicas**: Add read replicas for read-heavy workloads
- **Connection Pooling**: Implement connection pooling in the application

## Troubleshooting

### Common Issues

1. **Connection Timeouts**: Check firewall rules and network configuration
2. **SSL Errors**: Ensure SSL is properly configured
3. **Authentication Failures**: Verify username and password
4. **Performance Issues**: Monitor resource usage and consider scaling

### Useful Commands

```bash
# Check server status
az mysql flexible-server show --name <server-name> --resource-group <resource-group>

# View firewall rules
az mysql flexible-server firewall-rule list --name <server-name> --resource-group <resource-group>

# Test connection
mysql -h <server-fqdn> -u <username> -p
```

## Cleanup

To remove all resources:

```bash
terraform destroy
```

**Warning**: This will permanently delete the database and all data!