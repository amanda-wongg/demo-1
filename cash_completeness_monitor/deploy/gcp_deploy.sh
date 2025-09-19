#!/bin/bash
# Google Cloud Functions deployment script for Cash Completeness Monitor

set -e

# Configuration
FUNCTION_NAME="cash-completeness-monitor"
RUNTIME="python39"
ENTRY_POINT="cash_monitor_pubsub"
MEMORY="256MB"
TIMEOUT="300s"
REGION="us-central1"
SCHEDULE="0 7 * * *"  # Daily at 7 AM UTC
TOPIC_NAME="cash-monitor-trigger"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Google Cloud Functions deployment for Cash Completeness Monitor${NC}"

# Check if gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No active Google Cloud project. Run 'gcloud config set project PROJECT_ID'${NC}"
    exit 1
fi

echo -e "${YELLOW}Deploying to project: $PROJECT_ID${NC}"

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable pubsub.googleapis.com

# Create Pub/Sub topic if it doesn't exist
echo -e "${YELLOW}Creating Pub/Sub topic...${NC}"
gcloud pubsub topics create "$TOPIC_NAME" 2>/dev/null || echo "Topic already exists"

# Deploy the function
echo -e "${YELLOW}Deploying Cloud Function...${NC}"
cd ..

gcloud functions deploy "$FUNCTION_NAME" \
    --runtime="$RUNTIME" \
    --trigger-topic="$TOPIC_NAME" \
    --entry-point="$ENTRY_POINT" \
    --memory="$MEMORY" \
    --timeout="$TIMEOUT" \
    --region="$REGION" \
    --source=. \
    --quiet

echo -e "${GREEN}Cloud Function deployed successfully${NC}"

# Create Cloud Scheduler job
echo -e "${YELLOW}Setting up Cloud Scheduler job...${NC}"

JOB_NAME="cash-monitor-daily-trigger"

# Delete existing job if it exists
gcloud scheduler jobs delete "$JOB_NAME" --location="$REGION" --quiet 2>/dev/null || true

# Create new job
gcloud scheduler jobs create pubsub "$JOB_NAME" \
    --location="$REGION" \
    --schedule="$SCHEDULE" \
    --topic="$TOPIC_NAME" \
    --message-body='{"source":"cloud-scheduler","scheduled":true}' \
    --description="Daily trigger for Cash Completeness Monitor"

echo -e "${GREEN}Cloud Scheduler job created successfully${NC}"

cd deploy

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Function Name: $FUNCTION_NAME${NC}"
echo -e "${YELLOW}Schedule: Daily at 7 AM UTC${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo -e "${YELLOW}Project: $PROJECT_ID${NC}"

echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Set environment variables for the Cloud Function:"
echo -e "   gcloud functions deploy $FUNCTION_NAME --update-env-vars REDASH_BASE_URL=your_url,REDASH_API_KEY=your_key,SLACK_BOT_TOKEN=your_token,SLACK_CHANNEL=your_channel"
echo -e "2. Test the function manually:"
echo -e "   gcloud pubsub topics publish $TOPIC_NAME --message '{\"test\": true}'"
echo -e "3. Monitor the function logs:"
echo -e "   gcloud functions logs read $FUNCTION_NAME --region=$REGION"