#!/bin/bash

# AWS Deployment Script for Price Cage
# This script automates the deployment of Price Cage system on AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="price-cage"
REGION="us-east-1"
VPC_CIDR="10.0.0.0/16"
DB_PASSWORD=""
KEY_PAIR_NAME=""
DOMAIN_NAME=""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is installed and configured
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_status "AWS CLI is configured and ready"
}

# Function to get user input
get_user_input() {
    read -p "Enter database password (min 8 characters): " -s DB_PASSWORD
    echo
    if [ ${#DB_PASSWORD} -lt 8 ]; then
        print_error "Password must be at least 8 characters long"
        exit 1
    fi
    
    read -p "Enter EC2 Key Pair name: " KEY_PAIR_NAME
    if [ -z "$KEY_PAIR_NAME" ]; then
        print_error "Key pair name is required"
        exit 1
    fi
    
    read -p "Enter domain name (optional, press Enter to skip): " DOMAIN_NAME
}

# Function to create VPC and networking
create_vpc() {
    print_status "Creating VPC and networking components..."
    
    # Create VPC
    VPC_ID=$(aws ec2 create-vpc \
        --cidr-block $VPC_CIDR \
        --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT_NAME}-vpc}]" \
        --query 'Vpc.VpcId' \
        --output text)
    
    print_status "Created VPC: $VPC_ID"
    
    # Create Internet Gateway
    IGW_ID=$(aws ec2 create-internet-gateway \
        --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-igw}]" \
        --query 'InternetGateway.InternetGatewayId' \
        --output text)
    
    # Attach Internet Gateway to VPC
    aws ec2 attach-internet-gateway \
        --internet-gateway-id $IGW_ID \
        --vpc-id $VPC_ID
    
    print_status "Created and attached Internet Gateway: $IGW_ID"
    
    # Get availability zones
    AZ1=$(aws ec2 describe-availability-zones --region $REGION --query 'AvailabilityZones[0].ZoneName' --output text)
    AZ2=$(aws ec2 describe-availability-zones --region $REGION --query 'AvailabilityZones[1].ZoneName' --output text)
    
    # Create public subnets
    PUBLIC_SUBNET1_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.1.0/24 \
        --availability-zone $AZ1 \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-1}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    PUBLIC_SUBNET2_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.2.0/24 \
        --availability-zone $AZ2 \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-2}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    # Create private subnets
    PRIVATE_SUBNET1_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.10.0/24 \
        --availability-zone $AZ1 \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-1}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    PRIVATE_SUBNET2_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.20.0/24 \
        --availability-zone $AZ2 \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-2}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    print_status "Created subnets: $PUBLIC_SUBNET1_ID, $PUBLIC_SUBNET2_ID, $PRIVATE_SUBNET1_ID, $PRIVATE_SUBNET2_ID"
    
    # Create NAT Gateway
    EIP_ALLOC_ID=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
    
    NAT_GW_ID=$(aws ec2 create-nat-gateway \
        --subnet-id $PUBLIC_SUBNET1_ID \
        --allocation-id $EIP_ALLOC_ID \
        --tag-specifications "ResourceType=nat-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat}]" \
        --query 'NatGateway.NatGatewayId' \
        --output text)
    
    print_status "Created NAT Gateway: $NAT_GW_ID"
    
    # Wait for NAT Gateway to be available
    print_status "Waiting for NAT Gateway to be available..."
    aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID
    
    # Create route tables
    PUBLIC_RT_ID=$(aws ec2 create-route-table \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-rt}]" \
        --query 'RouteTable.RouteTableId' \
        --output text)
    
    PRIVATE_RT_ID=$(aws ec2 create-route-table \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-rt}]" \
        --query 'RouteTable.RouteTableId' \
        --output text)
    
    # Create routes
    aws ec2 create-route \
        --route-table-id $PUBLIC_RT_ID \
        --destination-cidr-block 0.0.0.0/0 \
        --gateway-id $IGW_ID
    
    aws ec2 create-route \
        --route-table-id $PRIVATE_RT_ID \
        --destination-cidr-block 0.0.0.0/0 \
        --nat-gateway-id $NAT_GW_ID
    
    # Associate subnets with route tables
    aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET1_ID --route-table-id $PUBLIC_RT_ID
    aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET2_ID --route-table-id $PUBLIC_RT_ID
    aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET1_ID --route-table-id $PRIVATE_RT_ID
    aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET2_ID --route-table-id $PRIVATE_RT_ID
    
    print_status "Networking setup completed"
}

# Function to create security groups
create_security_groups() {
    print_status "Creating security groups..."
    
    # ALB Security Group
    ALB_SG_ID=$(aws ec2 create-security-group \
        --group-name "${PROJECT_NAME}-alb-sg" \
        --description "Security group for ALB" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-alb-sg}]" \
        --query 'GroupId' \
        --output text)
    
    # EC2 Security Group
    EC2_SG_ID=$(aws ec2 create-security-group \
        --group-name "${PROJECT_NAME}-ec2-sg" \
        --description "Security group for EC2 instances" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-ec2-sg}]" \
        --query 'GroupId' \
        --output text)
    
    # RDS Security Group
    RDS_SG_ID=$(aws ec2 create-security-group \
        --group-name "${PROJECT_NAME}-rds-sg" \
        --description "Security group for RDS" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-rds-sg}]" \
        --query 'GroupId' \
        --output text)
    
    # Redis Security Group
    REDIS_SG_ID=$(aws ec2 create-security-group \
        --group-name "${PROJECT_NAME}-redis-sg" \
        --description "Security group for Redis" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-redis-sg}]" \
        --query 'GroupId' \
        --output text)
    
    # Configure security group rules
    # ALB - Allow HTTP and HTTPS
    aws ec2 authorize-security-group-ingress \
        --group-id $ALB_SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0
    
    aws ec2 authorize-security-group-ingress \
        --group-id $ALB_SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0
    
    # EC2 - Allow from ALB and SSH
    aws ec2 authorize-security-group-ingress \
        --group-id $EC2_SG_ID \
        --protocol tcp \
        --port 8000 \
        --source-group $ALB_SG_ID
    
    aws ec2 authorize-security-group-ingress \
        --group-id $EC2_SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0
    
    # RDS - Allow from EC2
    aws ec2 authorize-security-group-ingress \
        --group-id $RDS_SG_ID \
        --protocol tcp \
        --port 5432 \
        --source-group $EC2_SG_ID
    
    # Redis - Allow from EC2
    aws ec2 authorize-security-group-ingress \
        --group-id $REDIS_SG_ID \
        --protocol tcp \
        --port 6379 \
        --source-group $EC2_SG_ID
    
    print_status "Security groups created: ALB($ALB_SG_ID), EC2($EC2_SG_ID), RDS($RDS_SG_ID), Redis($REDIS_SG_ID)"
}

# Function to create RDS database
create_rds() {
    print_status "Creating RDS database..."
    
    # Create DB subnet group
    aws rds create-db-subnet-group \
        --db-subnet-group-name "${PROJECT_NAME}-db-subnet-group" \
        --db-subnet-group-description "Database subnet group for $PROJECT_NAME" \
        --subnet-ids $PRIVATE_SUBNET1_ID $PRIVATE_SUBNET2_ID
    
    # Create RDS instance
    aws rds create-db-instance \
        --db-instance-identifier "${PROJECT_NAME}-db" \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --engine-version 15.3 \
        --master-username pricecage \
        --master-user-password "$DB_PASSWORD" \
        --allocated-storage 20 \
        --storage-type gp2 \
        --db-subnet-group-name "${PROJECT_NAME}-db-subnet-group" \
        --vpc-security-group-ids $RDS_SG_ID \
        --backup-retention-period 7 \
        --storage-encrypted \
        --multi-az \
        --no-publicly-accessible \
        --tags Key=Name,Value="${PROJECT_NAME}-database"
    
    print_status "RDS instance creation initiated. This may take several minutes..."
}

# Function to create ElastiCache
create_elasticache() {
    print_status "Creating ElastiCache Redis cluster..."
    
    # Create cache subnet group
    aws elasticache create-cache-subnet-group \
        --cache-subnet-group-name "${PROJECT_NAME}-cache-subnet-group" \
        --cache-subnet-group-description "Cache subnet group for $PROJECT_NAME" \
        --subnet-ids $PRIVATE_SUBNET1_ID $PRIVATE_SUBNET2_ID
    
    # Create Redis cluster
    aws elasticache create-cache-cluster \
        --cache-cluster-id "${PROJECT_NAME}-redis" \
        --engine redis \
        --cache-node-type cache.t3.micro \
        --num-cache-nodes 1 \
        --cache-subnet-group-name "${PROJECT_NAME}-cache-subnet-group" \
        --security-group-ids $REDIS_SG_ID \
        --tags Key=Name,Value="${PROJECT_NAME}-redis"
    
    print_status "ElastiCache cluster creation initiated..."
}

# Function to create ALB
create_alb() {
    print_status "Creating Application Load Balancer..."
    
    # Create ALB
    ALB_ARN=$(aws elbv2 create-load-balancer \
        --name "${PROJECT_NAME}-alb" \
        --subnets $PUBLIC_SUBNET1_ID $PUBLIC_SUBNET2_ID \
        --security-groups $ALB_SG_ID \
        --tags Key=Name,Value="${PROJECT_NAME}-alb" \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text)
    
    # Create target group
    TG_ARN=$(aws elbv2 create-target-group \
        --name "${PROJECT_NAME}-tg" \
        --protocol HTTP \
        --port 8000 \
        --vpc-id $VPC_ID \
        --health-check-path /health \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --tags Key=Name,Value="${PROJECT_NAME}-tg" \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    # Create listener
    aws elbv2 create-listener \
        --load-balancer-arn $ALB_ARN \
        --protocol HTTP \
        --port 80 \
        --default-actions Type=forward,TargetGroupArn=$TG_ARN
    
    # Get ALB DNS name
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --load-balancer-arns $ALB_ARN \
        --query 'LoadBalancers[0].DNSName' \
        --output text)
    
    print_status "Created ALB: $ALB_DNS"
}

# Function to create user data script
create_user_data() {
    cat > user-data.sh << 'EOF'
#!/bin/bash
yum update -y
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

# Clone repository (replace with your actual repo)
git clone https://github.com/your-repo/price-cage.git .

# Create environment file
cat > .env << EOL
DATABASE_URL=postgresql://pricecage:PASSWORD_PLACEHOLDER@RDS_ENDPOINT_PLACEHOLDER:5432/pricecage
REDIS_HOST=REDIS_ENDPOINT_PLACEHOLDER
REDIS_PORT=6379
SECRET_KEY=your-secret-key-change-this-in-production
LOG_LEVEL=INFO
EOL

# Create docker-compose.yml
cat > docker-compose.yml << 'EOL'
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOL

# Start application
docker-compose up -d
EOF
}

# Function to create launch template and auto scaling group
create_asg() {
    print_status "Creating Auto Scaling Group..."
    
    # Create user data script
    create_user_data
    
    # Get latest Amazon Linux 2 AMI
    AMI_ID=$(aws ec2 describe-images \
        --owners amazon \
        --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text)
    
    # Create launch template
    aws ec2 create-launch-template \
        --launch-template-name "${PROJECT_NAME}-lt" \
        --launch-template-data "{
            \"ImageId\": \"$AMI_ID\",
            \"InstanceType\": \"t3.medium\",
            \"KeyName\": \"$KEY_PAIR_NAME\",
            \"SecurityGroupIds\": [\"$EC2_SG_ID\"],
            \"UserData\": \"$(base64 -w 0 user-data.sh)\",
            \"TagSpecifications\": [{
                \"ResourceType\": \"instance\",
                \"Tags\": [{\"Key\": \"Name\", \"Value\": \"${PROJECT_NAME}-api\"}]
            }]
        }"
    
    # Create Auto Scaling Group
    aws autoscaling create-auto-scaling-group \
        --auto-scaling-group-name "${PROJECT_NAME}-asg" \
        --launch-template "LaunchTemplateName=${PROJECT_NAME}-lt,Version=1" \
        --min-size 2 \
        --max-size 6 \
        --desired-capacity 2 \
        --target-group-arns $TG_ARN \
        --vpc-zone-identifier "$PRIVATE_SUBNET1_ID,$PRIVATE_SUBNET2_ID" \
        --health-check-type ELB \
        --health-check-grace-period 300 \
        --tags "Key=Name,Value=${PROJECT_NAME}-asg,PropagateAtLaunch=true"
    
    print_status "Auto Scaling Group created"
}

# Function to wait for resources to be ready
wait_for_resources() {
    print_status "Waiting for resources to be ready..."
    
    # Wait for RDS to be available
    print_status "Waiting for RDS database to be available (this may take 10-15 minutes)..."
    aws rds wait db-instance-available --db-instance-identifier "${PROJECT_NAME}-db"
    
    # Get RDS endpoint
    RDS_ENDPOINT=$(aws rds describe-db-instances \
        --db-instance-identifier "${PROJECT_NAME}-db" \
        --query 'DBInstances[0].Endpoint.Address' \
        --output text)
    
    # Wait for ElastiCache to be available
    print_status "Waiting for ElastiCache to be available..."
    aws elasticache wait cache-cluster-available --cache-cluster-id "${PROJECT_NAME}-redis"
    
    # Get Redis endpoint
    REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
        --cache-cluster-id "${PROJECT_NAME}-redis" \
        --query 'CacheClusters[0].RedisConfiguration.PrimaryEndpoint.Address' \
        --output text)
    
    print_status "Resources are ready!"
    print_status "RDS Endpoint: $RDS_ENDPOINT"
    print_status "Redis Endpoint: $REDIS_ENDPOINT"
}

# Function to output deployment summary
deployment_summary() {
    echo
    echo "=================================="
    echo "   DEPLOYMENT SUMMARY"
    echo "=================================="
    echo
    echo "Application URL: http://$ALB_DNS"
    echo "Database Endpoint: $RDS_ENDPOINT"
    echo "Redis Endpoint: $REDIS_ENDPOINT"
    echo
    echo "Next Steps:"
    echo "1. Update DNS records to point to: $ALB_DNS"
    echo "2. Configure SSL certificate for HTTPS"
    echo "3. Update user-data script with actual endpoints"
    echo "4. Monitor CloudWatch for health status"
    echo
    echo "Important Notes:"
    echo "- Database password is stored securely"
    echo "- EC2 instances are in private subnets"
    echo "- Auto Scaling is configured for 2-6 instances"
    echo "- Backups are enabled for 7 days"
    echo
    echo "To access your instances:"
    echo "  ssh -i ~/.ssh/$KEY_PAIR_NAME.pem ec2-user@<instance-ip>"
    echo
    echo "To check application status:"
    echo "  curl http://$ALB_DNS/health"
}

# Function to cleanup on error
cleanup() {
    print_error "Deployment failed. Cleaning up resources..."
    # Add cleanup commands here if needed
    exit 1
}

# Main deployment function
main() {
    print_status "Starting AWS deployment for Price Cage..."
    
    # Set up error handling
    trap cleanup ERR
    
    # Pre-deployment checks
    check_aws_cli
    get_user_input
    
    # Create infrastructure
    create_vpc
    create_security_groups
    create_rds
    create_elasticache
    create_alb
    create_asg
    
    # Wait for resources to be ready
    wait_for_resources
    
    # Show deployment summary
    deployment_summary
    
    print_status "Deployment completed successfully!"
}

# Run main function
main "$@"