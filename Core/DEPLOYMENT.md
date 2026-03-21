# 🚀 Deployment Guide

## Local Development

### Option 1: Running Locally (Development)
```bash
# Already set up! Just run:
python main.py
```

### Option 2: Using Docker (Optional)
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GEMINI_API_KEY=${GEMINI_API_KEY}

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t adaptive-learning-backend .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here adaptive-learning-backend
```

---

## Production Deployment

### Using Gunicorn + FastAPI
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker main:app
```

### Using Heroku
Create `Procfile`:
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT --worker-class uvicorn.workers.UvicornWorker main:app
```

Deploy:
```bash
heroku create your-app-name
heroku config:set GEMINI_API_KEY=your_key_here
git push heroku main
```

### Using AWS EC2

1. **Launch EC2 instance** (Ubuntu 22.04)

2. **SSH into instance**:
```bash
ssh -i key.pem ubuntu@your-instance-ip
```

3. **Install dependencies**:
```bash
sudo apt update
sudo apt install python3.11 python3-pip python3-venv
```

4. **Clone repository**:
```bash
git clone your-repo
cd backend1
```

5. **Setup and run**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
gunicorn -w 4 -b 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker main:app
```

6. **Use systemd service** (for auto-restart):
Create `/etc/systemd/system/adaptive-learning.service`:
```ini
[Unit]
Description=Adaptive Learning Platform Backend
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/backend1
Environment="GEMINI_API_KEY=your_key"
ExecStart=/home/ubuntu/backend1/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 main:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable adaptive-learning
sudo systemctl start adaptive-learning
```

### Using Google Cloud Run

1. **Create `app.yaml`**:
```yaml
runtime: python311
entrypoint: gunicorn -w 4 -b 0.0.0.0:$PORT --worker-class uvicorn.workers.UvicornWorker main:app
env_variables:
  GEMINI_API_KEY: "your_key_here"
```

2. **Deploy**:
```bash
gcloud app deploy app.yaml
```

---

## Database Considerations

### Local Development (SQLite)
- Simple, no setup needed
- Good for development and testing
- Located in `adaptive_learning.db`

### Production (PostgreSQL)
Update `database.py`:
```python
import psycopg2

# Instead of:
self.conn = sqlite3.connect(self.db_path)

# Use:
self.conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
```

---

## Performance Optimization

### 1. Database Optimization
```python
# Add indexes in database.py
cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_answers ON user_answers(user_id, exercise_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_topic_perf ON topic_performance(user_id, topic)')
```

### 2. Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_exercise(exercise_id: str):
    # Cached database queries
    return db.get_exercise(exercise_id)
```

### 3. Async Database
```python
# Use async SQLAlchemy in production
from sqlalchemy.ext.asyncio import create_async_engine
engine = create_async_engine('postgresql+asyncpg://...')
```

### 4. Load Balancing
```nginx
# nginx configuration
upstream adaptive_learning {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://adaptive_learning;
    }
}
```

---

## Security Checklist

- [ ] **API Key Management**
  - Use environment variables, not hardcoded
  - Rotate keys regularly
  - Use secrets manager (AWS Secrets Manager, Google Secret Manager)

- [ ] **Authentication**
  - Add JWT token validation
  - Implement rate limiting
  - Add API key authentication

- [ ] **Database Security**
  - Use connection pooling
  - Encrypt sensitive data
  - Regular backups
  - Use strong passwords

- [ ] **Network Security**
  - Enable HTTPS/SSL
  - Use CORS appropriately
  - Add DDoS protection
  - Firewall rules

- [ ] **Code Security**
  - Dependency scanning (Snyk, OWASP)
  - Regular security updates
  - SQL injection prevention (already handled by Pydantic)
  - XSS prevention
  - CSRF protection

---

## Monitoring & Logging

### Add Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In endpoints:
logger.info(f"User {user_id} answered question {exercise_id}")
logger.error(f"Failed to generate question: {error}")
```

### Monitor Performance
```bash
# Install monitoring tools
pip install prometheus-client
```

### Log Aggregation
- Use services like CloudWatch, DataDog, ELK Stack
- Monitor error rates
- Track API response times
- Monitor database performance

---

## Scaling Considerations

### Horizontal Scaling
1. **Load Balancer**: Distribute requests across multiple instances
2. **Database**: Separate database server
3. **Cache**: Redis for caching frequently accessed data
4. **APIs**: Queue system (Celery) for async tasks

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Use better hardware

---

## Example Production Environment

```bash
# Install production server
pip install gunicorn uvicorn python-dotenv

# Environment variables
export GEMINI_API_KEY=your_key_here
export DATABASE_URL=postgresql://user:pass@host/dbname
export WORKERS=4
export PORT=8000

# Run with gunicorn
gunicorn -w $WORKERS -b 0.0.0.0:$PORT \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-logfile - \
  --error-logfile - \
  main:app
```

---

## CI/CD Pipeline

### GitHub Actions Example
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest test_backend.py -v
      
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: |
          # Your deployment script
          ./deploy.sh
```

---

## Troubleshooting Deployment

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Out of Memory
```bash
# Check memory usage
free -h

# Limit worker processes
gunicorn -w 2 -b 0.0.0.0:8000 main:app
```

### Database Connection Issues
```bash
# Test database connection
python -c "import sqlite3; print('OK')"

# For PostgreSQL
python -c "import psycopg2; psycopg2.connect(...); print('OK')"
```

---

## Backup & Recovery

### Database Backup
```bash
# SQLite
cp adaptive_learning.db adaptive_learning.db.backup

# PostgreSQL
pg_dump database_name > backup.sql

# Restore
psql database_name < backup.sql
```

### Automated Backups
```bash
# Add to crontab
0 2 * * * /home/ubuntu/backup_database.sh
```

---

## Performance Benchmarking

### Load Testing
```bash
# Install Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Or use locust
pip install locust
locust -f locustfile.py
```

---

## Further Reading

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn Configuration](https://docs.gunicorn.org/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Security Best Practices](https://owasp.org/www-project-top-ten/)

---

**Start with local development, then deploy to production when ready!**
