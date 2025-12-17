# Deployment Guide

## Local Development

```bash
# 1. Setup
cp -r /path/to/original/services ./
pip install -r requirements.txt
mkdir -p data/{config,db,consolidated}

# 2. Configure
# Edit data/config/company_info.json

# 3. Run
reflex init  # First time only
reflex run
```

## Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY services/ ./services/

RUN reflex init

EXPOSE 3000 8000

CMD ["reflex", "run", "--env", "prod"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  reflex-paie:
    build: .
    ports:
      - "3000:3000"
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - PYTHONUNBUFFERED=1
```

**Deploy:**
```bash
docker-compose up -d
```

## Reflex Cloud

```bash
# 1. Install CLI
pip install reflex[cloud]

# 2. Login
reflex login

# 3. Deploy
reflex deploy

# 4. Configure secrets
reflex secrets set DB_PATH=/data/db/payroll.duckdb
```

**Pricing:** ~$20-50/month depending on usage

## Production Checklist

- [ ] Environment variables for sensitive data
- [ ] HTTPS/SSL certificate
- [ ] Database backups scheduled
- [ ] Error monitoring (Sentry)
- [ ] User analytics (optional)
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Admin account secured
- [ ] SMTP configured (for emails)
- [ ] Domain configured

## Environment Variables

```bash
# .env
DB_PATH=/data/db/payroll.duckdb
CONFIG_PATH=/data/config
UPLOAD_PATH=/data/uploads
EXPORT_PATH=/data/exports
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ADMIN_EMAIL=admin@company.mc
```

## Monitoring

**Application logs:**
```bash
reflex run --loglevel info
```

**Database health:**
```python
import duckdb
conn = duckdb.connect('data/db/payroll.duckdb')
print(conn.execute("SELECT COUNT(*) FROM payroll_data").fetchone())
```

**Disk usage:**
```bash
du -sh data/
```

## Backup Strategy

**Daily backups:**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d)
tar -czf backups/paie-$DATE.tar.gz data/
# Keep 30 days
find backups/ -mtime +30 -delete
```

**Cron:**
```cron
0 2 * * * /app/backup.sh
```

## Security Hardening

1. **Firewall:** Only open 3000, 8000
2. **Auth:** Strong passwords, 2FA (future)
3. **Database:** Encrypted at rest
4. **Uploads:** Scan for malware
5. **API:** Rate limiting
6. **Logs:** No sensitive data logged

## Troubleshooting

**Port conflicts:**
```bash
reflex run --frontend-port 3001 --backend-port 8001
```

**Database locked:**
```python
# Force close connections
import duckdb
conn = duckdb.connect('data/db/payroll.duckdb')
conn.execute("CHECKPOINT")
conn.close()
```

**Memory issues:**
```bash
# Increase limits
docker run -m 4g reflex-paie
```

## Migration from Streamlit

1. **Export all data** from Streamlit to Excel
2. **Setup Reflex** with same directory structure
3. **Import data** via Import page
4. **Verify calculations** match Streamlit
5. **Run in parallel** for 1 month
6. **Switch over** once confident

## Support

**Issues:** GitHub issues
**Docs:** README.md, PROJECT_STATUS.md
**Contact:** admin@company.mc
