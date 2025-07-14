# AWS Deployment Guide for Price Cage

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Hardware Requirements & Cost Estimation](#hardware-requirements--cost-estimation)
3. [AWS Services Selection](#aws-services-selection)
4. [Infrastructure Setup](#infrastructure-setup)
5. [Step-by-Step Deployment](#step-by-step-deployment)
6. [Configuration Files](#configuration-files)
7. [Security Setup](#security-setup)
8. [Monitoring & Backup](#monitoring--backup)
9. [Maintenance & Updates](#maintenance--updates)
10. [Cost Optimization](#cost-optimization)

## Architecture Overview

### Recommended AWS Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                               │
│                                                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   CloudFront    │    │   Application   │    │   Database  │ │
│  │   (CDN/Cache)   │    │   Load Balancer │    │   Services  │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                       │                     │      │
│           │              ┌─────────────────┐            │      │
│           │              │   Auto Scaling  │            │      │
│           │              │     Group       │            │      │
│           │              └─────────────────┘            │      │
│           │                       │                     │      │
│           │              ┌─────────────────┐            │      │
│           │              │   EC2 Instances │            │      │
│           │              │   (API Servers) │            │      │
│           │              └─────────────────┘            │      │
│           │                       │                     │      │
│           │              ┌─────────────────┐    ┌─────────────┐ │
│           │              │   ECS Cluster   │    │   RDS       │ │
│           │              │   (Crawlers)    │    │ PostgreSQL  │ │
│           │              └─────────────────┘    └─────────────┘ │
│           │                       │                     │      │
│           │              ┌─────────────────┐    ┌─────────────┐ │
│           │              │   ElastiCache   │    │   S3        │ │
│           │              │   (Redis)       │    │ (Backups)   │ │
│           │              └─────────────────┘    └─────────────┘ │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

## Hardware Requirements & Cost Estimation

### Traffic Assumptions (Small to Medium Scale)
- **Daily API requests**: ~100,000
- **Concurrent users**: ~50-100
- **Data storage**: ~10GB/month growth
- **Backup retention**: 30 days

### AWS Services & Estimated Monthly Costs

#### Compute Services
| Service | Instance Type | Quantity | Monthly Cost (USD) | Purpose |
|---------|---------------|----------|-------------------|---------|
| EC2 (API) | t3.medium | 2 | $60.74 | API servers |
| ECS Fargate | 0.5 vCPU, 1GB RAM | 2 tasks | $21.60 | Crawler tasks |
| ALB | Application Load Balancer | 1 | $16.20 | Load balancing |

#### Database Services
| Service | Instance Type | Storage | Monthly Cost (USD) | Purpose |
|---------|---------------|---------|-------------------|---------|
| RDS PostgreSQL | db.t3.micro | 20GB | $15.73 | Main database |
| ElastiCache | cache.t3.micro | 1 node | $13.14 | Redis cache |

#### Storage & CDN
| Service | Usage | Monthly Cost (USD) | Purpose |
|---------|-------|-------------------|---------|
| S3 | 50GB storage | $1.15 | Backups, static files |
| CloudFront | 100GB transfer | $8.50 | CDN, static content |

#### Networking & Security
| Service | Usage | Monthly Cost (USD) | Purpose |
|---------|-------|-------------------|---------|
| VPC | Standard | $0.00 | Network isolation |
| NAT Gateway | 1 instance | $32.40 | Outbound internet |
| Route 53 | 1 hosted zone | $0.50 | DNS management |
| ACM | SSL certificates | $0.00 | HTTPS encryption |

#### Monitoring & Logging
| Service | Usage | Monthly Cost (USD) | Purpose |
|---------|-------|-------------------|---------|
| CloudWatch | Standard metrics | $10.00 | Monitoring |
| CloudWatch Logs | 10GB/month | $5.00 | Log aggregation |

### **Total Estimated Monthly Cost: ~$185-220 USD**

## AWS Services Selection

### Core Services
1. **EC2**: API server hosting
2. **ECS Fargate**: Containerized crawler services
3. **RDS PostgreSQL**: Primary database
4. **ElastiCache**: Redis caching layer
5. **Application Load Balancer**: Traffic distribution
6. **S3**: Static files and backups
7. **CloudFront**: CDN for improved performance

### Supporting Services
1. **VPC**: Network isolation
2. **Security Groups**: Firewall rules
3. **IAM**: Access management
4. **CloudWatch**: Monitoring and alerting
5. **Systems Manager**: Configuration management
6. **Auto Scaling**: Automatic scaling

## Infrastructure Setup

### 1. VPC Configuration
```yaml
# VPC Setup
VPC CIDR: 10.0.0.0/16
Availability Zones: 2 (us-east-1a, us-east-1b)

Subnets:
- Public Subnet A: 10.0.1.0/24 (us-east-1a)
- Public Subnet B: 10.0.2.0/24 (us-east-1b)
- Private Subnet A: 10.0.10.0/24 (us-east-1a)
- Private Subnet B: 10.0.20.0/24 (us-east-1b)
```

### 2. Security Groups
```yaml
# ALB Security Group
ALB-SG:
  Inbound:
    - Port 80 (HTTP): 0.0.0.0/0
    - Port 443 (HTTPS): 0.0.0.0/0
  Outbound:
    - All traffic to EC2-SG

# EC2 Security Group
EC2-SG:
  Inbound:
    - Port 8000: ALB-SG
    - Port 22: Admin IP ranges
  Outbound:
    - All traffic: 0.0.0.0/0

# RDS Security Group
RDS-SG:
  Inbound:
    - Port 5432: EC2-SG, ECS-SG
  Outbound:
    - None

# ElastiCache Security Group
CACHE-SG:
  Inbound:
    - Port 6379: EC2-SG, ECS-SG
  Outbound:
    - None
```

## Step-by-Step Deployment

### Phase 1: Infrastructure Setup

#### Step 1: Create VPC and Networking
```bash
# Create VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=price-cage-vpc}]'

# Create Internet Gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=price-cage-igw}]'

# Attach Internet Gateway to VPC
aws ec2 attach-internet-gateway \
  --internet-gateway-id igw-xxxxxxxxx \
  --vpc-id vpc-xxxxxxxxx

# Create Subnets
aws ec2 create-subnet \
  --vpc-id vpc-xxxxxxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=price-cage-public-1a}]'

aws ec2 create-subnet \
  --vpc-id vpc-xxxxxxxxx \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=price-cage-public-1b}]'

aws ec2 create-subnet \
  --vpc-id vpc-xxxxxxxxx \
  --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=price-cage-private-1a}]'

aws ec2 create-subnet \
  --vpc-id vpc-xxxxxxxxx \
  --cidr-block 10.0.20.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=price-cage-private-1b}]'
```

#### Step 2: Create NAT Gateway
```bash
# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Create NAT Gateway
aws ec2 create-nat-gateway \
  --subnet-id subnet-xxxxxxxxx \
  --allocation-id eipalloc-xxxxxxxxx \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=price-cage-nat}]'
```

#### Step 3: Create Route Tables
```bash
# Create route table for public subnets
aws ec2 create-route-table \
  --vpc-id vpc-xxxxxxxxx \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=price-cage-public-rt}]'

# Create route table for private subnets
aws ec2 create-route-table \
  --vpc-id vpc-xxxxxxxxx \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=price-cage-private-rt}]'

# Add routes
aws ec2 create-route \
  --route-table-id rtb-xxxxxxxxx \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-xxxxxxxxx

aws ec2 create-route \
  --route-table-id rtb-xxxxxxxxx \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id nat-xxxxxxxxx
```

### Phase 2: Database Setup

#### Step 1: Create RDS Subnet Group
```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name price-cage-db-subnet-group \
  --db-subnet-group-description "Price Cage Database Subnet Group" \
  --subnet-ids subnet-xxxxxxxxx subnet-yyyyyyyyy
```

#### Step 2: Create RDS Instance
```bash
aws rds create-db-instance \
  --db-instance-identifier price-cage-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username pricecage \
  --master-user-password YourSecurePassword123! \
  --allocated-storage 20 \
  --storage-type gp2 \
  --db-subnet-group-name price-cage-db-subnet-group \
  --vpc-security-group-ids sg-xxxxxxxxx \
  --backup-retention-period 7 \
  --storage-encrypted \
  --multi-az \
  --tags Key=Name,Value=price-cage-database
```

#### Step 3: Create ElastiCache Subnet Group
```bash
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name price-cage-cache-subnet-group \
  --cache-subnet-group-description "Price Cage Cache Subnet Group" \
  --subnet-ids subnet-xxxxxxxxx subnet-yyyyyyyyy
```

#### Step 4: Create ElastiCache Cluster
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id price-cage-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --cache-subnet-group-name price-cage-cache-subnet-group \
  --security-group-ids sg-xxxxxxxxx
```

### Phase 3: Application Deployment

#### Step 1: Create Application Load Balancer
```bash
aws elbv2 create-load-balancer \
  --name price-cage-alb \
  --subnets subnet-xxxxxxxxx subnet-yyyyyyyyy \
  --security-groups sg-xxxxxxxxx \
  --tags Key=Name,Value=price-cage-alb
```

#### Step 2: Create Target Group
```bash
aws elbv2 create-target-group \
  --name price-cage-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxxxxxx \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3
```

#### Step 3: Create Launch Template
```bash
aws ec2 create-launch-template \
  --launch-template-name price-cage-lt \
  --launch-template-data '{
    "ImageId": "ami-0abcdef1234567890",
    "InstanceType": "t3.medium",
    "KeyName": "your-key-pair",
    "SecurityGroupIds": ["sg-xxxxxxxxx"],
    "UserData": "$(base64 -w 0 user-data.sh)",
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [{"Key": "Name", "Value": "price-cage-api"}]
    }]
  }'
```

### Phase 4: Auto Scaling Setup

#### Step 1: Create Auto Scaling Group
```bash
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name price-cage-asg \
  --launch-template "LaunchTemplateName=price-cage-lt,Version=1" \
  --min-size 2 \
  --max-size 6 \
  --desired-capacity 2 \
  --target-group-arns arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/price-cage-tg/1234567890123456 \
  --vpc-zone-identifier "subnet-xxxxxxxxx,subnet-yyyyyyyyy" \
  --health-check-type ELB \
  --health-check-grace-period 300
```

#### Step 2: Create Scaling Policies
```bash
# Scale Up Policy
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name price-cage-asg \
  --policy-name price-cage-scale-up \
  --scaling-adjustment 1 \
  --adjustment-type ChangeInCapacity \
  --cooldown 300

# Scale Down Policy
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name price-cage-asg \
  --policy-name price-cage-scale-down \
  --scaling-adjustment -1 \
  --adjustment-type ChangeInCapacity \
  --cooldown 300
```

### Phase 5: ECS Setup for Crawlers

#### Step 1: Create ECS Cluster
```bash
aws ecs create-cluster \
  --cluster-name price-cage-crawlers \
  --capacity-providers FARGATE \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
```

#### Step 2: Register Task Definition
```bash
aws ecs register-task-definition \
  --cli-input-json file://crawler-task-definition.json
```

#### Step 3: Create ECS Service
```bash
aws ecs create-service \
  --cluster price-cage-crawlers \
  --service-name price-cage-crawler-service \
  --task-definition price-cage-crawler \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxxx,subnet-yyyyyyyyy],securityGroups=[sg-xxxxxxxxx],assignPublicIp=DISABLED}"
```

## Configuration Files

### 1. User Data Script for EC2 Instances
```bash
#!/bin/bash
# user-data.sh

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Create application directory
mkdir -p /opt/price-cage
cd /opt/price-cage

# Download application code (replace with your S3 bucket or ECR)
aws s3 cp s3://your-bucket/price-cage.tar.gz .
tar -xzf price-cage.tar.gz

# Create environment file
cat > .env << EOF
DATABASE_URL=postgresql://pricecage:YourSecurePassword123!@${RDS_ENDPOINT}:5432/pricecage
REDIS_HOST=${REDIS_ENDPOINT}
REDIS_PORT=6379
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
EOF

# Create docker-compose.yml for production
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=${LOG_LEVEL}
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
    restart: always
EOF

# Create nginx configuration
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        
        location /health {
            proxy_pass http://api;
            access_log off;
        }
        
        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Start the application
docker-compose -f docker-compose.prod.yml up -d

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "metrics": {
    "namespace": "PriceCage",
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/price-cage/logs/api.log",
            "log_group_name": "/aws/ec2/price-cage/api",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
```

### 2. ECS Task Definition for Crawlers
```json
{
  "family": "price-cage-crawler",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "price-cage-crawler",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/price-cage-crawler:latest",
      "essential": true,
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://pricecage:YourSecurePassword123!@RDS_ENDPOINT:5432/pricecage"
        },
        {
          "name": "REDIS_HOST",
          "value": "REDIS_ENDPOINT"
        },
        {
          "name": "REDIS_PORT",
          "value": "6379"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:price-cage-secrets:SECRET_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/price-cage-crawler",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "command": ["python", "scripts/run_crawler.py", "--schedule"]
    }
  ]
}
```

### 3. CloudFormation Template
```yaml
# cloudformation-template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Price Cage Infrastructure'

Parameters:
  DBPassword:
    Type: String
    NoEcho: true
    Description: Database password
    MinLength: 8
    
  KeyPairName:
    Type: AWS::EC2::KeyPair::KeyName
    Description: EC2 Key Pair for SSH access

Resources:
  # VPC
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: price-cage-vpc

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: price-cage-igw

  InternetGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      InternetGatewayId: !Ref InternetGateway
      VpcId: !Ref VPC

  # Public Subnets
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.0.1.0/24
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: price-cage-public-subnet-1

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: 10.0.2.0/24
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: price-cage-public-subnet-2

  # Private Subnets
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.0.10.0/24
      Tags:
        - Key: Name
          Value: price-cage-private-subnet-1

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: 10.0.20.0/24
      Tags:
        - Key: Name
          Value: price-cage-private-subnet-2

  # NAT Gateway
  NatGateway1EIP:
    Type: AWS::EC2::EIP
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc

  NatGateway1:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatGateway1EIP.AllocationId
      SubnetId: !Ref PublicSubnet1

  # Route Tables
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: price-cage-public-rt

  DefaultPublicRoute:
    Type: AWS::EC2::Route
    DependsOn: InternetGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet1

  PublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet2

  PrivateRouteTable1:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: price-cage-private-rt-1

  DefaultPrivateRoute1:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway1

  PrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      SubnetId: !Ref PrivateSubnet1

  PrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      SubnetId: !Ref PrivateSubnet2

  # RDS Database
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS database
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
      Tags:
        - Key: Name
          Value: price-cage-db-subnet-group

  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: price-cage-db
      DBInstanceClass: db.t3.micro
      Engine: postgres
      EngineVersion: '15.3'
      MasterUsername: pricecage
      MasterUserPassword: !Ref DBPassword
      AllocatedStorage: 20
      StorageType: gp2
      DBSubnetGroupName: !Ref DBSubnetGroup
      VPCSecurityGroups:
        - !Ref DatabaseSecurityGroup
      BackupRetentionPeriod: 7
      StorageEncrypted: true
      MultiAZ: true
      Tags:
        - Key: Name
          Value: price-cage-database

Outputs:
  VPCId:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub "${AWS::StackName}-VPC-ID"

  DatabaseEndpoint:
    Description: Database endpoint
    Value: !GetAtt Database.Endpoint.Address
    Export:
      Name: !Sub "${AWS::StackName}-DB-Endpoint"
```

## Security Setup

### 1. IAM Roles and Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 2. Security Groups Rules
```bash
# Create security groups
aws ec2 create-security-group \
  --group-name price-cage-alb-sg \
  --description "Security group for ALB" \
  --vpc-id vpc-xxxxxxxxx

aws ec2 create-security-group \
  --group-name price-cage-ec2-sg \
  --description "Security group for EC2 instances" \
  --vpc-id vpc-xxxxxxxxx

aws ec2 create-security-group \
  --group-name price-cage-rds-sg \
  --description "Security group for RDS" \
  --vpc-id vpc-xxxxxxxxx
```

### 3. SSL Certificate Setup
```bash
# Request SSL certificate
aws acm request-certificate \
  --domain-name yourdomain.com \
  --domain-name www.yourdomain.com \
  --validation-method DNS \
  --tags Key=Name,Value=price-cage-cert
```

## Monitoring & Backup

### 1. CloudWatch Alarms
```bash
# CPU Utilization Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "price-cage-high-cpu" \
  --alarm-description "High CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### 2. Backup Strategy
```bash
# Create S3 bucket for backups
aws s3 mb s3://price-cage-backups-unique-name

# Create backup script
cat > backup-script.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_$DATE.sql"

# Create database backup
pg_dump -h $RDS_ENDPOINT -U pricecage -d pricecage > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE.gz s3://price-cage-backups-unique-name/

# Cleanup local file
rm $BACKUP_FILE.gz
EOF
```

## Maintenance & Updates

### 1. Auto Scaling Policies
```bash
# Create CloudWatch alarms for scaling
aws cloudwatch put-metric-alarm \
  --alarm-name "price-cage-scale-up-alarm" \
  --alarm-description "Scale up when CPU > 70%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:autoscaling:us-east-1:123456789012:scalingPolicy:policy-id
```

### 2. Update Strategy
```bash
# Blue-Green deployment script
#!/bin/bash
# 1. Create new launch template version
# 2. Update auto scaling group
# 3. Wait for health checks
# 4. Terminate old instances
```

## Cost Optimization

### 1. Reserved Instances
- Consider 1-year reserved instances for predictable workloads
- Potential savings: 30-40% on EC2 costs

### 2. Spot Instances
- Use spot instances for non-critical crawler tasks
- Potential savings: 50-70% on compute costs

### 3. Scheduled Scaling
```bash
# Scale down during off-peak hours
aws autoscaling put-scheduled-update-group-action \
  --auto-scaling-group-name price-cage-asg \
  --scheduled-action-name "scale-down-night" \
  --recurrence "0 22 * * *" \
  --desired-capacity 1 \
  --min-size 1 \
  --max-size 1
```

## Deployment Timeline

### Week 1: Infrastructure Setup
- Day 1-2: Create VPC, subnets, security groups
- Day 3-4: Set up RDS, ElastiCache
- Day 5-7: Configure ALB, Auto Scaling

### Week 2: Application Deployment
- Day 8-10: Deploy API servers
- Day 11-12: Set up ECS for crawlers
- Day 13-14: Configure monitoring, backups

### Week 3: Testing & Optimization
- Day 15-17: Load testing
- Day 18-19: Performance tuning
- Day 20-21: Security hardening

## Total Implementation Cost

### One-time Setup Costs
- SSL Certificate: $0 (AWS ACM)
- Initial configuration: ~$50 (engineer time)

### Monthly Operating Costs
- **Infrastructure**: ~$185-220/month
- **Data Transfer**: ~$10-20/month
- **Monitoring**: ~$15-25/month

### **Total Monthly Cost: ~$210-265 USD**

This AWS deployment provides a robust, scalable solution for the Price Cage system with automatic scaling, monitoring, and backup capabilities suitable for small to medium traffic volumes.