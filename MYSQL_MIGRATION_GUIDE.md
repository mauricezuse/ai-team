# MySQL Migration Guide

This guide helps you migrate from SQLite to Azure Database for MySQL to resolve database locking issues.

## 🚨 Why Migrate to MySQL?

**Current Issues with SQLite:**
- ❌ Database lock errors: `(sqlite3.OperationalError) database is locked`
- ❌ Concurrent access limitations
- ❌ QueuePool timeout errors
- ❌ Not suitable for production AI orchestration

**Benefits of MySQL:**
- ✅ True concurrent access with proper locking
- ✅ Built-in connection pooling
- ✅ High availability and reliability
- ✅ Scalable for production workloads
- ✅ ACID compliance for data integrity

## 📋 Prerequisites

1. **Azure CLI** installed and configured
2. **Terraform** installed (version >= 1.0)
3. **Python** with PyMySQL driver
4. **Azure subscription** with appropriate permissions

## 🚀 Step 1: Deploy Azure Database for MySQL

### 1.1 Configure Azure CLI

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "Your-Subscription-ID"
```

### 1.2 Deploy Infrastructure

```bash
# Navigate to terraform directory
cd infra/terraform

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
nano terraform.tfvars
```

**Important**: Update the `mysql_admin_password` with a strong password!

### 1.3 Deploy with Terraform

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy the infrastructure
terraform apply
```

### 1.4 Get Connection Information

```bash
# Get connection details
terraform output connection_string
terraform output mysql_server_fqdn
terraform output mysql_database_name
```

## 🔧 Step 2: Configure Application

### 2.1 Install MySQL Driver

```bash
# Install PyMySQL
pip install PyMySQL

# Add to requirements.txt
echo "PyMySQL>=1.0.2" >> requirements.txt
```

### 2.2 Set Environment Variables

```bash
# Set MySQL connection details
export MYSQL_HOST="your-server.mysql.database.azure.com"
export MYSQL_PORT="3306"
export MYSQL_DATABASE="ai_team"
export MYSQL_USERNAME="ai_team_admin"
export MYSQL_PASSWORD="your_secure_password"

# Or set DATABASE_URL directly
export DATABASE_URL="mysql+pymysql://username:password@host:port/database"
```

### 2.3 Update Database Configuration

Replace the database import in your application:

```python
# OLD: from crewai_app.database import get_db, Workflow, Conversation
# NEW: from crewai_app.database_mysql import get_db, Workflow, Conversation
```

## 📦 Step 3: Migrate Data

### 3.1 Run Migration Script

```bash
# Set MySQL environment variables
export MYSQL_HOST="your-server.mysql.database.azure.com"
export MYSQL_PASSWORD="your_secure_password"

# Run migration
python migrate_to_mysql.py
```

### 3.2 Verify Migration

The migration script will:
- ✅ Connect to both SQLite and MySQL
- ✅ Migrate all tables and data
- ✅ Verify row counts match
- ✅ Report any issues

## 🔄 Step 4: Update Application

### 4.1 Update Database Imports

Update all files that import from `crewai_app.database`:

```python
# Change from:
from crewai_app.database import get_db, Workflow, Conversation

# To:
from crewai_app.database_mysql import get_db, Workflow, Conversation
```

### 4.2 Update Main Application

Update `crewai_app/main.py`:

```python
# Change database import
from crewai_app.database_mysql import get_db, create_tables

# Initialize MySQL tables
create_tables()
```

### 4.3 Update Services

Update service files:
- `crewai_app/services/conversation_service.py`
- `crewai_app/services/workflow_status_service.py`
- `crewai_app/services/workflow_executor.py`

## 🧪 Step 5: Test the Migration

### 5.1 Start the Application

```bash
# Start the server
source venv/bin/activate
uvicorn crewai_app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 Test API Endpoints

```bash
# Test workflows endpoint
curl -X GET http://localhost:8000/workflows

# Test workflow creation
curl -X POST http://localhost:8000/workflows/from-jira/NEGISHI-165

# Test resume functionality
curl -X POST http://localhost:8000/workflows/2/resume
```

### 5.3 Monitor Logs

```bash
# Check for database errors
tail -f backend.log | grep -i "database\|mysql\|error"

# Check for connection issues
tail -f backend.log | grep -i "connection\|pool"
```

## 🔍 Step 6: Verify Performance

### 6.1 Check Connection Pool

```python
# Test connection pooling
from crewai_app.database_mysql import engine
print(f"Pool size: {engine.pool.size()}")
print(f"Checked out: {engine.pool.checkedout()}")
```

### 6.2 Monitor Database Performance

- **Connection Count**: Should be stable, not growing
- **Query Performance**: Should be faster than SQLite
- **Lock Contention**: Should be eliminated

## 🚨 Troubleshooting

### Common Issues

#### 1. Connection Errors

```bash
# Error: Can't connect to MySQL server
# Solution: Check firewall rules and credentials
```

**Fix:**
```bash
# Check Azure firewall rules
az mysql flexible-server firewall-rule list --name <server-name> --resource-group <resource-group>

# Add your IP to firewall
az mysql flexible-server firewall-rule create --name <server-name> --resource-group <resource-group> --rule-name "MyIP" --start-ip-address <your-ip> --end-ip-address <your-ip>
```

#### 2. SSL Certificate Errors

```bash
# Error: SSL certificate verification failed
# Solution: Update connection string
```

**Fix:**
```python
# Add SSL parameters to connection string
DATABASE_URL = "mysql+pymysql://user:pass@host:port/db?ssl_disabled=false&ssl_verify_cert=true&ssl_verify_identity=true"
```

#### 3. Authentication Failures

```bash
# Error: Access denied for user
# Solution: Check username and password
```

**Fix:**
```bash
# Verify credentials
mysql -h <server-fqdn> -u <username> -p
```

### Performance Issues

#### 1. Slow Queries

```sql
-- Check slow queries
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Slow_queries';
```

#### 2. Connection Pool Exhaustion

```python
# Monitor connection pool
from crewai_app.database_mysql import engine
print(f"Pool size: {engine.pool.size()}")
print(f"Checked out: {engine.pool.checkedout()}")
print(f"Overflow: {engine.pool.overflow()}")
```

## 📊 Monitoring and Maintenance

### 1. Azure Monitor

- **CPU Usage**: Monitor server CPU
- **Memory Usage**: Track memory consumption
- **Connection Count**: Monitor active connections
- **Storage Usage**: Track database size

### 2. Application Monitoring

```python
# Add database health checks
@app.get("/health/database")
async def database_health():
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "mysql"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 3. Backup and Recovery

- **Automated Backups**: 7-day retention (configurable)
- **Point-in-Time Recovery**: Available for up to 35 days
- **Cross-Region Backup**: Consider for disaster recovery

## 🎯 Expected Results

After migration, you should see:

- ✅ **No more database lock errors**
- ✅ **Improved concurrent performance**
- ✅ **Stable connection pooling**
- ✅ **Better scalability**
- ✅ **Production-ready database**

## 📝 Next Steps

1. **Monitor Performance**: Track database metrics
2. **Optimize Queries**: Add indexes as needed
3. **Scale Resources**: Adjust SKU based on usage
4. **Implement Monitoring**: Set up alerts and dashboards
5. **Backup Strategy**: Configure automated backups

## 🆘 Support

If you encounter issues:

1. **Check Logs**: Review `backend.log` for errors
2. **Verify Configuration**: Ensure all environment variables are set
3. **Test Connectivity**: Use `mysql` client to test connection
4. **Review Azure Portal**: Check server status and metrics
5. **Contact Support**: Use Azure support if needed

---

**🎉 Congratulations!** You've successfully migrated from SQLite to Azure Database for MySQL, eliminating the database locking issues and providing a robust, scalable database solution for your AI orchestration platform.
