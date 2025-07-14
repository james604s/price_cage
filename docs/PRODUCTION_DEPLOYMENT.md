# Production Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Deployment Options](#deployment-options)
4. [Security Considerations](#security-considerations)
5. [Performance Optimization](#performance-optimization)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Backup and Recovery](#backup-and-recovery)
8. [Scaling Strategy](#scaling-strategy)
9. [Maintenance and Updates](#maintenance-and-updates)

## Overview

This guide provides comprehensive recommendations for deploying the Price Cage system in a production environment. The system requires careful consideration of security, performance, scalability, and reliability.

## Infrastructure Requirements

### Minimum Hardware Requirements
- **CPU**: 4 cores (8 cores recommended)
- **RAM**: 8GB (16GB recommended)
- **Storage**: 100GB SSD (500GB recommended)
- **Network**: 100Mbps (1Gbps recommended)

### Recommended Cloud Infrastructure
- **AWS**: EC2 instances (t3.large or higher)
- **Google Cloud**: Compute Engine (n1-standard-4 or higher)
- **Azure**: Virtual Machines (Standard D4s v3 or higher)

### Database Requirements
- **PostgreSQL**: Version 13 or higher
- **Redis**: Version 6 or higher
- **Storage**: Minimum 100GB for database, auto-scaling recommended

## Deployment Options

### Option 1: Docker Compose (Recommended for Small to Medium Scale)

#### Production Docker Compose Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - api
    restart: always

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: price_cage_prod
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: always
    command: postgres -c max_connections=200 -c shared_buffers=256MB

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always

  # API Service (Multiple instances)
  api:
    build: .
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/price_cage_prod
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    depends_on:
      - postgres
      - redis
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Celery Worker
  celery-worker:
    build: .
    command: celery -A src.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/price_cage_prod
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    depends_on:
      - postgres
      - redis
    restart: always
    deploy:
      replicas: 2

  # Celery Beat Scheduler
  celery-beat:
    build: .
    command: celery -A src.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/price_cage_prod
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    depends_on:
      - postgres
      - redis
    restart: always

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: always

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    restart: always

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

#### Nginx Configuration

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            proxy_pass http://api;
            access_log off;
        }
    }
}
```

### Option 2: Kubernetes (Recommended for Large Scale)

#### Kubernetes Deployment Configuration

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: price-cage
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: price-cage-config
  namespace: price-cage
data:
  DATABASE_URL: "postgresql://user:password@postgres:5432/price_cage"
  REDIS_HOST: "redis"
  LOG_LEVEL: "INFO"
---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: price-cage-secrets
  namespace: price-cage
type: Opaque
data:
  db-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
  secret-key: <base64-encoded-secret-key>
---
# k8s/deployment-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: price-cage-api
  namespace: price-cage
spec:
  replicas: 3
  selector:
    matchLabels:
      app: price-cage-api
  template:
    metadata:
      labels:
        app: price-cage-api
    spec:
      containers:
      - name: api
        image: price-cage:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: price-cage-config
              key: DATABASE_URL
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: price-cage-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: price-cage-api-service
  namespace: price-cage
spec:
  selector:
    app: price-cage-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: price-cage-api-hpa
  namespace: price-cage
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: price-cage-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Option 3: Cloud Native Services

#### AWS Deployment
```yaml
# AWS ECS Task Definition
{
  "family": "price-cage-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "price-cage-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/price-cage:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:password@rds-endpoint:5432/price_cage"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:price-cage-secrets"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/price-cage-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Security Considerations

### 1. SSL/TLS Configuration
```bash
# Generate SSL certificate
sudo certbot certonly --webroot -w /var/www/html -d your-domain.com

# Auto-renewal
0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Environment Variables Security
```env
# Production .env (store in secure location)
DATABASE_URL=postgresql://user:secure_password@db:5432/price_cage
SECRET_KEY=very-long-random-secret-key-here
REDIS_PASSWORD=secure-redis-password
```

### 3. Network Security
```yaml
# Docker network isolation
networks:
  backend:
    driver: bridge
    internal: true
  frontend:
    driver: bridge
```

### 4. Database Security
```sql
-- Create dedicated database user
CREATE USER price_cage_prod WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE price_cage_prod TO price_cage_prod;
GRANT USAGE ON SCHEMA public TO price_cage_prod;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO price_cage_prod;
```

### 5. API Security
```python
# Rate limiting configuration
RATE_LIMIT_ENABLED = True
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000

# CORS configuration
CORS_ORIGINS = ["https://your-domain.com"]
CORS_CREDENTIALS = True
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Index optimization
CREATE INDEX CONCURRENTLY idx_products_category_price ON products(category, current_price);
CREATE INDEX CONCURRENTLY idx_price_history_product_date ON price_history(product_id, recorded_at);

-- Connection pooling
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
```

### 2. Redis Configuration
```conf
# redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. Application Optimization
```python
# Connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_POOL_OVERFLOW = 0
DATABASE_POOL_RECYCLE = 3600

# Async processing
CELERY_WORKER_CONCURRENCY = 4
CELERY_TASK_ROUTES = {
    'crawler.tasks': {'queue': 'crawler'},
    'analytics.tasks': {'queue': 'analytics'}
}
```

## Monitoring and Logging

### 1. Prometheus Configuration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'price-cage-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']
```

### 2. Grafana Dashboards
```json
{
  "dashboard": {
    "title": "Price Cage Monitoring",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends"
          }
        ]
      }
    ]
  }
}
```

### 3. Centralized Logging
```yaml
# ELK Stack configuration
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    
  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    
  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
```

## Backup and Recovery

### 1. Database Backup Strategy
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="price_cage_prod"

# Create backup
pg_dump -h postgres -U price_cage_user -d $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/
```

### 2. Automated Backup Schedule
```yaml
# k8s/cronjob-backup.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command: ["/bin/sh", "-c"]
            args:
            - |
              pg_dump -h postgres -U price_cage_user -d price_cage_prod | gzip > /backup/backup_$(date +%Y%m%d).sql.gz
          restartPolicy: OnFailure
```

### 3. Disaster Recovery Plan
```markdown
## Recovery Procedures

### Database Recovery
1. Stop all services
2. Restore from latest backup
3. Apply transaction logs if available
4. Restart services in order

### Application Recovery
1. Deploy previous stable version
2. Verify database connectivity
3. Run health checks
4. Gradually increase traffic
```

## Scaling Strategy

### 1. Horizontal Scaling
```yaml
# Auto-scaling configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: price-cage-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: price-cage-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 2. Database Scaling
```sql
-- Read replicas configuration
-- Master-slave setup for read scaling
CREATE PUBLICATION price_cage_pub FOR ALL TABLES;
```

### 3. Caching Strategy
```python
# Redis cluster configuration
REDIS_CLUSTER_NODES = [
    {"host": "redis-node-1", "port": 7000},
    {"host": "redis-node-2", "port": 7000},
    {"host": "redis-node-3", "port": 7000}
]
```

## Maintenance and Updates

### 1. Blue-Green Deployment
```yaml
# Blue-Green deployment script
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: price-cage-api
spec:
  strategy:
    blueGreen:
      activeService: price-cage-api-active
      previewService: price-cage-api-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
```

### 2. Database Migrations
```python
# Migration script
from alembic import command
from alembic.config import Config

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

### 3. Health Checks
```python
# Health check endpoint
@app.get("/health")
async def health_check():
    checks = {
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }
    
    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail="Service unhealthy")
```

## Deployment Checklist

### Pre-Deployment
- [ ] Security review completed
- [ ] Performance testing passed
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] SSL certificates installed
- [ ] Environment variables secured

### Deployment
- [ ] Blue-green deployment ready
- [ ] Database migrations tested
- [ ] Health checks passing
- [ ] Load balancer configured
- [ ] CDN configured (if applicable)

### Post-Deployment
- [ ] Monitor system metrics
- [ ] Verify all endpoints working
- [ ] Check log aggregation
- [ ] Validate backup procedures
- [ ] Test disaster recovery
- [ ] Document any issues

## Cost Optimization

### 1. Resource Right-Sizing
```yaml
# Resource optimization
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 2. Spot Instances (AWS)
```yaml
# Spot instance configuration
nodeSelector:
  node.kubernetes.io/instance-type: "spot"
tolerations:
- key: "spot"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```

### 3. Storage Optimization
```yaml
# Storage classes
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
```

This comprehensive deployment guide provides multiple options for deploying Price Cage in production environments, from simple Docker Compose setups to enterprise-grade Kubernetes deployments. Choose the option that best fits your scale, budget, and operational requirements.