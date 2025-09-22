#!/usr/bin/env python3
"""
Redash-Slack AI Workflow Integration
A comprehensive service that connects Redash and Slack with AI-powered insights
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
import schedule
import time
from threading import Thread

from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@dataclass
class RedashQuery:
    """Data class for Redash query information"""
    id: int
    name: str
    query: str
    data_source_id: int
    updated_at: str
    results: Optional[Dict] = None

@dataclass
class WorkflowConfig:
    """Configuration for workflow automation"""
    name: str
    redash_query_id: int
    slack_channel: str
    schedule_cron: str
    alert_conditions: Dict[str, Any]
    ai_insights_enabled: bool = True

class RedashClient:
    """Client for interacting with Redash API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Key {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def execute_query(self, query_id: int) -> Dict:
        """Execute a Redash query and return results"""
        async with aiohttp.ClientSession() as session:
            # Refresh query results
            refresh_url = f"{self.base_url}/api/queries/{query_id}/refresh"
            async with session.post(refresh_url, headers=self.headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to refresh query {query_id}: {response.status}")
                
                job_data = await response.json()
                job_id = job_data['job']['id']
            
            # Poll for results
            results_url = f"{self.base_url}/api/jobs/{job_id}"
            for _ in range(30):  # Poll for up to 30 seconds
                async with session.get(results_url, headers=self.headers) as response:
                    if response.status != 200:
                        continue
                    
                    job_status = await response.json()
                    if job_status['job']['status'] == 3:  # Completed
                        query_result_id = job_status['job']['query_result_id']
                        break
                    elif job_status['job']['status'] == 4:  # Failed
                        raise Exception(f"Query {query_id} execution failed")
                    
                    await asyncio.sleep(1)
            else:
                raise Exception(f"Query {query_id} execution timeout")
            
            # Get query results
            result_url = f"{self.base_url}/api/query_results/{query_result_id}"
            async with session.get(result_url, headers=self.headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get query results: {response.status}")
                
                return await response.json()
    
    async def get_query_info(self, query_id: int) -> RedashQuery:
        """Get information about a specific query"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/queries/{query_id}"
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get query info: {response.status}")
                
                data = await response.json()
                return RedashQuery(
                    id=data['id'],
                    name=data['name'],
                    query=data['query'],
                    data_source_id=data['data_source_id'],
                    updated_at=data['updated_at']
                )
    
    async def get_dashboard_info(self, dashboard_id: int) -> Dict:
        """Get dashboard information and widgets"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/dashboards/{dashboard_id}"
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get dashboard info: {response.status}")
                
                return await response.json()

class SlackBot:
    """Slack bot for handling interactions and notifications"""
    
    def __init__(self, bot_token: str, signing_secret: str):
        self.client = WebClient(token=bot_token)
        self.signing_secret = signing_secret
    
    async def send_message(self, channel: str, text: str, blocks: Optional[List[Dict]] = None):
        """Send a message to a Slack channel"""
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            return response
        except SlackApiError as e:
            logger.error(f"Error sending Slack message: {e.response['error']}")
            raise
    
    def create_data_blocks(self, query_name: str, data: List[Dict], insights: str = None) -> List[Dict]:
        """Create Slack blocks for displaying data and insights"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 {query_name}"
                }
            }
        ]
        
        # Add data preview (first 5 rows)
        if data:
            preview_data = data[:5]
            fields = []
            
            for row in preview_data:
                for key, value in row.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:* {value}"
                    })
            
            blocks.append({
                "type": "section",
                "fields": fields[:10]  # Limit to 10 fields per section
            })
            
            if len(data) > 5:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Showing 5 of {len(data)} rows_"
                        }
                    ]
                })
        
        # Add AI insights if available
        if insights:
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🤖 *AI Insights:*\n{insights}"
                    }
                }
            ])
        
        return blocks
    
    def create_alert_blocks(self, query_name: str, condition: str, current_value: Any, threshold: Any) -> List[Dict]:
        """Create Slack blocks for alerts"""
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Alert Triggered"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Query:* {query_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Condition:* {condition}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Value:* {current_value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Threshold:* {threshold}"
                    }
                ]
            }
        ]

class AIInsightsEngine:
    """AI-powered insights engine for data analysis"""
    
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
    
    async def generate_insights(self, query_name: str, data: List[Dict], query_sql: str = None) -> str:
        """Generate AI insights from query results"""
        try:
            # Prepare data summary for AI analysis
            data_summary = self._prepare_data_summary(data)
            
            prompt = f"""
            Analyze the following data from a query named "{query_name}" and provide actionable insights:
            
            Data Summary:
            {data_summary}
            
            {f"SQL Query: {query_sql}" if query_sql else ""}
            
            Please provide:
            1. Key findings and trends
            2. Potential concerns or anomalies
            3. Actionable recommendations
            4. Questions to investigate further
            
            Keep the response concise and business-focused.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data analyst providing insights on business data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "Unable to generate AI insights at this time."
    
    def _prepare_data_summary(self, data: List[Dict]) -> str:
        """Prepare a summary of the data for AI analysis"""
        if not data:
            return "No data available"
        
        # Get basic statistics
        row_count = len(data)
        columns = list(data[0].keys()) if data else []
        
        summary = f"Rows: {row_count}\nColumns: {', '.join(columns)}\n\n"
        
        # Sample data (first few rows)
        sample_size = min(3, len(data))
        summary += f"Sample data (first {sample_size} rows):\n"
        for i, row in enumerate(data[:sample_size]):
            summary += f"Row {i+1}: {json.dumps(row, default=str)}\n"
        
        return summary

class WorkflowManager:
    """Manages automated workflows and scheduling"""
    
    def __init__(self, redash_client: RedashClient, slack_bot: SlackBot, ai_engine: AIInsightsEngine):
        self.redash_client = redash_client
        self.slack_bot = slack_bot
        self.ai_engine = ai_engine
        self.workflows: Dict[str, WorkflowConfig] = {}
    
    def add_workflow(self, config: WorkflowConfig):
        """Add a new workflow configuration"""
        self.workflows[config.name] = config
        logger.info(f"Added workflow: {config.name}")
    
    async def execute_workflow(self, workflow_name: str):
        """Execute a specific workflow"""
        if workflow_name not in self.workflows:
            logger.error(f"Workflow {workflow_name} not found")
            return
        
        config = self.workflows[workflow_name]
        
        try:
            # Execute Redash query
            logger.info(f"Executing query {config.redash_query_id} for workflow {workflow_name}")
            query_info = await self.redash_client.get_query_info(config.redash_query_id)
            results = await self.redash_client.execute_query(config.redash_query_id)
            
            data = results.get('query_result', {}).get('data', {}).get('rows', [])
            
            # Check alert conditions
            alert_triggered = self._check_alert_conditions(data, config.alert_conditions)
            
            # Generate AI insights if enabled
            insights = None
            if config.ai_insights_enabled:
                insights = await self.ai_engine.generate_insights(
                    query_info.name, 
                    data, 
                    query_info.query
                )
            
            # Send to Slack
            if alert_triggered:
                # Send alert
                alert_blocks = self.slack_bot.create_alert_blocks(
                    query_info.name,
                    str(config.alert_conditions),
                    alert_triggered['value'],
                    alert_triggered['threshold']
                )
                await self.slack_bot.send_message(
                    config.slack_channel,
                    f"Alert triggered for {query_info.name}",
                    alert_blocks
                )
            else:
                # Send regular update
                blocks = self.slack_bot.create_data_blocks(query_info.name, data, insights)
                await self.slack_bot.send_message(
                    config.slack_channel,
                    f"Data update for {query_info.name}",
                    blocks
                )
            
            logger.info(f"Workflow {workflow_name} executed successfully")
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_name}: {e}")
            # Send error notification to Slack
            await self.slack_bot.send_message(
                config.slack_channel,
                f"❌ Error executing workflow {workflow_name}: {str(e)}"
            )
    
    def _check_alert_conditions(self, data: List[Dict], conditions: Dict[str, Any]) -> Optional[Dict]:
        """Check if alert conditions are met"""
        if not conditions or not data:
            return None
        
        try:
            condition_type = conditions.get('type')
            field = conditions.get('field')
            threshold = conditions.get('threshold')
            operator = conditions.get('operator', 'gt')  # gt, lt, eq, gte, lte
            
            if not all([condition_type, field, threshold is not None]):
                return None
            
            if condition_type == 'value':
                # Check specific field value
                for row in data:
                    if field in row:
                        value = row[field]
                        if self._evaluate_condition(value, operator, threshold):
                            return {'value': value, 'threshold': threshold}
            
            elif condition_type == 'count':
                # Check row count
                count = len(data)
                if self._evaluate_condition(count, operator, threshold):
                    return {'value': count, 'threshold': threshold}
            
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
        
        return None
    
    def _evaluate_condition(self, value: Any, operator: str, threshold: Any) -> bool:
        """Evaluate a condition"""
        try:
            if operator == 'gt':
                return value > threshold
            elif operator == 'lt':
                return value < threshold
            elif operator == 'gte':
                return value >= threshold
            elif operator == 'lte':
                return value <= threshold
            elif operator == 'eq':
                return value == threshold
            elif operator == 'ne':
                return value != threshold
        except Exception:
            pass
        return False

# Global instances
redash_client = None
slack_bot = None
ai_engine = None
workflow_manager = None

def initialize_services():
    """Initialize all services with environment variables"""
    global redash_client, slack_bot, ai_engine, workflow_manager
    
    # Environment variables
    redash_url = os.getenv('REDASH_URL')
    redash_api_key = os.getenv('REDASH_API_KEY')
    slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
    slack_signing_secret = os.getenv('SLACK_SIGNING_SECRET')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not all([redash_url, redash_api_key, slack_bot_token, openai_api_key]):
        logger.error("Missing required environment variables")
        return False
    
    try:
        redash_client = RedashClient(redash_url, redash_api_key)
        slack_bot = SlackBot(slack_bot_token, slack_signing_secret)
        ai_engine = AIInsightsEngine(openai_api_key)
        workflow_manager = WorkflowManager(redash_client, slack_bot, ai_engine)
        
        logger.info("All services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        return False

# Flask routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/webhook/slack', methods=['POST'])
def slack_webhook():
    """Handle Slack webhook events"""
    try:
        data = request.json
        
        # Handle different event types
        if data.get('type') == 'url_verification':
            return jsonify({'challenge': data.get('challenge')})
        
        # Handle slash commands
        if 'command' in data:
            return handle_slash_command(data)
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        logger.error(f"Error handling Slack webhook: {e}")
        return jsonify({'error': str(e)}), 500

def handle_slash_command(data: Dict) -> Dict:
    """Handle Slack slash commands"""
    command = data.get('command')
    text = data.get('text', '').strip()
    channel_id = data.get('channel_id')
    
    if command == '/redash-query':
        # Execute a Redash query
        try:
            query_id = int(text)
            # Schedule async execution
            asyncio.create_task(execute_query_command(query_id, channel_id))
            return jsonify({
                'response_type': 'in_channel',
                'text': f'Executing Redash query {query_id}...'
            })
        except ValueError:
            return jsonify({
                'response_type': 'ephemeral',
                'text': 'Please provide a valid query ID'
            })
    
    elif command == '/redash-workflow':
        # Manage workflows
        parts = text.split()
        if len(parts) >= 2 and parts[0] == 'run':
            workflow_name = parts[1]
            asyncio.create_task(workflow_manager.execute_workflow(workflow_name))
            return jsonify({
                'response_type': 'in_channel',
                'text': f'Executing workflow: {workflow_name}'
            })
    
    return jsonify({
        'response_type': 'ephemeral',
        'text': 'Unknown command or invalid parameters'
    })

async def execute_query_command(query_id: int, channel_id: str):
    """Execute a query command asynchronously"""
    try:
        query_info = await redash_client.get_query_info(query_id)
        results = await redash_client.execute_query(query_id)
        
        data = results.get('query_result', {}).get('data', {}).get('rows', [])
        
        # Generate AI insights
        insights = await ai_engine.generate_insights(
            query_info.name, 
            data, 
            query_info.query
        )
        
        # Send results to Slack
        blocks = slack_bot.create_data_blocks(query_info.name, data, insights)
        await slack_bot.send_message(channel_id, f"Results for query {query_id}", blocks)
        
    except Exception as e:
        logger.error(f"Error executing query command: {e}")
        await slack_bot.send_message(
            channel_id, 
            f"❌ Error executing query {query_id}: {str(e)}"
        )

@app.route('/api/workflows', methods=['GET'])
def list_workflows():
    """List all configured workflows"""
    workflows = []
    for name, config in workflow_manager.workflows.items():
        workflows.append({
            'name': name,
            'query_id': config.redash_query_id,
            'channel': config.slack_channel,
            'schedule': config.schedule_cron,
            'ai_enabled': config.ai_insights_enabled
        })
    return jsonify({'workflows': workflows})

@app.route('/api/workflows', methods=['POST'])
def create_workflow():
    """Create a new workflow"""
    try:
        data = request.json
        config = WorkflowConfig(
            name=data['name'],
            redash_query_id=data['query_id'],
            slack_channel=data['channel'],
            schedule_cron=data['schedule'],
            alert_conditions=data.get('alert_conditions', {}),
            ai_insights_enabled=data.get('ai_enabled', True)
        )
        
        workflow_manager.add_workflow(config)
        
        return jsonify({'status': 'created', 'workflow': data['name']})
    
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/workflows/<workflow_name>/execute', methods=['POST'])
def execute_workflow_api(workflow_name: str):
    """Execute a workflow via API"""
    try:
        asyncio.create_task(workflow_manager.execute_workflow(workflow_name))
        return jsonify({'status': 'executing', 'workflow': workflow_name})
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return jsonify({'error': str(e)}), 500

def run_scheduler():
    """Run the scheduler in a separate thread"""
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    if initialize_services():
        # Start scheduler thread
        scheduler_thread = Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Run Flask app
        port = int(os.getenv('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logger.error("Failed to initialize services")