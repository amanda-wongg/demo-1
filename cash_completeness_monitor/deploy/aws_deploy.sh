#!/bin/bash
# AWS Lambda deployment script for Cash Completeness Monitor

set -e

# Configuration
FUNCTION_NAME="cash-completeness-monitor"
RUNTIME="python3.9"
HANDLER="lambda_handler.lambda_handler"
TIMEOUT=300
MEMORY_SIZE=256
REGION="us-east-1"
SCHEDULE_EXPRESSION="cron(0 7 * * ? *)"  # Daily at 7 AM UTC

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AWS Lambda deployment for Cash Completeness Monitor${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if zip is installed
if ! command -v zip &> /dev/null; then
    echo -e "${RED}Error: zip is not installed${NC}"
    exit 1
fi

# Create deployment package
echo -e "${YELLOW}Creating deployment package...${NC}"
rm -f cash-monitor-deployment.zip

# Create a temporary directory for the package
TEMP_DIR=$(mktemp -d)
cp -r ../* "$TEMP_DIR/" 2>/dev/null || true
cd "$TEMP_DIR"

# Install dependencies
pip install -r requirements.txt -t .

# Create the zip file
zip -r cash-monitor-deployment.zip . -x "*.git*" "*.DS_Store*" "deploy/*" "tests/*" "*.md"

# Move zip back to deploy directory
mv cash-monitor-deployment.zip -

cd -
mv "$TEMP_DIR/cash-monitor-deployment.zip" .

# Clean up temp directory
rm -rf "$TEMP_DIR"

echo -e "${GREEN}Deployment package created: cash-monitor-deployment.zip${NC}"

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
    echo -e "${YELLOW}Updating existing Lambda function...${NC}"
    
    # Update function code
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://cash-monitor-deployment.zip \
        --region "$REGION"
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --handler "$HANDLER" \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --region "$REGION"
    
    echo -e "${GREEN}Lambda function updated successfully${NC}"
else
    echo -e "${YELLOW}Creating new Lambda function...${NC}"
    
    # Create IAM role if it doesn't exist
    ROLE_NAME="cash-monitor-lambda-role"
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")
    
    if [ -z "$ROLE_ARN" ]; then
        echo -e "${YELLOW}Creating IAM role...${NC}"
        
        # Create trust policy
        cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
        
        # Create the role
        aws iam create-role \
            --role-name "$ROLE_NAME" \
            --assume-role-policy-document file://trust-policy.json
        
        # Attach basic execution policy
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        # Get the role ARN
        ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
        
        # Clean up temp file
        rm trust-policy.json
        
        # Wait for role to be available
        echo -e "${YELLOW}Waiting for IAM role to be available...${NC}"
        sleep 10
    fi
    
    # Create the Lambda function
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file fileb://cash-monitor-deployment.zip \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --region "$REGION" \
        --description "Automated Cash Completeness Monitor"
    
    echo -e "${GREEN}Lambda function created successfully${NC}"
fi

# Set up CloudWatch Events rule for scheduling
echo -e "${YELLOW}Setting up CloudWatch Events rule...${NC}"

RULE_NAME="cash-monitor-daily-trigger"

# Create or update the rule
aws events put-rule \
    --name "$RULE_NAME" \
    --schedule-expression "$SCHEDULE_EXPRESSION" \
    --description "Daily trigger for Cash Completeness Monitor" \
    --region "$REGION"

# Add permission for CloudWatch Events to invoke the Lambda function
aws lambda add-permission \
    --function-name "$FUNCTION_NAME" \
    --statement-id "AllowExecutionFromCloudWatch" \
    --action "lambda:InvokeFunction" \
    --principal "events.amazonaws.com" \
    --source-arn "arn:aws:events:$REGION:$(aws sts get-caller-identity --query Account --output text):rule/$RULE_NAME" \
    --region "$REGION" 2>/dev/null || echo "Permission already exists"

# Add the Lambda function as a target for the rule
FUNCTION_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text)

aws events put-targets \
    --rule "$RULE_NAME" \
    --targets "Id"="1","Arn"="$FUNCTION_ARN","Input"='{"source":"cloudwatch-events","scheduled":true}' \
    --region "$REGION"

echo -e "${GREEN}CloudWatch Events rule configured successfully${NC}"

# Clean up deployment package
rm cash-monitor-deployment.zip

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Function Name: $FUNCTION_NAME${NC}"
echo -e "${YELLOW}Schedule: Daily at 7 AM UTC${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"

echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Set environment variables for the Lambda function:"
echo -e "   - REDASH_BASE_URL"
echo -e "   - REDASH_API_KEY" 
echo -e "   - SLACK_BOT_TOKEN"
echo -e "   - SLACK_CHANNEL"
echo -e "   - REDASH_QUERIES (JSON string)"
echo -e "2. Test the function manually"
echo -e "3. Monitor the CloudWatch logs"