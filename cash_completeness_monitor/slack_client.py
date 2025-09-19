"""
Slack API Client for Cash Completeness Monitor
Handles sending alerts and notifications to Slack channels.
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class SlackClient:
    """Client for sending messages to Slack."""
    
    def __init__(self, token: str, channel: str, username: str = "Cash Monitor Bot"):
        """
        Initialize Slack client.
        
        Args:
            token: Slack bot token
            channel: Default channel to send messages to
            username: Bot username for messages
        """
        self.token = token
        self.default_channel = channel
        self.username = username
        self.base_url = "https://slack.com/api"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"Slack client initialized for channel: {channel}")
    
    def send_message(
        self, 
        text: str, 
        channel: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Slack.
        
        Args:
            text: Message text
            channel: Channel to send to (uses default if not specified)
            blocks: Slack blocks for rich formatting
            attachments: Message attachments
            
        Returns:
            API response
        """
        channel = channel or self.default_channel
        
        logger.info(f"Sending message to {channel}")
        
        payload = {
            'channel': channel,
            'text': text,
            'username': self.username,
            'icon_emoji': ':robot_face:'
        }
        
        if blocks:
            payload['blocks'] = blocks
        
        if attachments:
            payload['attachments'] = attachments
        
        try:
            url = urljoin(self.base_url, '/chat.postMessage')
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get('ok'):
                raise Exception(f"Slack API error: {result.get('error', 'Unknown error')}")
            
            logger.info("Message sent successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            raise
    
    def send_formatted_variance_alert(self, variance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a formatted variance alert with rich blocks."""
        
        # Determine severity color
        amount = abs(variance_data.get('delta_amount', 0))
        if amount > 50000:
            color = "danger"
            emoji = "🚨"
        elif amount > 10000:
            color = "warning" 
            emoji = "⚠️"
        else:
            color = "good"
            emoji = "🔍"
        
        # Create rich message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} New Cash Variance Detected"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Check Type:*\n{variance_data.get('check_type', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Account:*\n{variance_data.get('account', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Amount:*\n{variance_data.get('currency', 'USD')} {variance_data.get('delta_amount', 0):,.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Detected:*\n{variance_data.get('detection_date', 'Unknown')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Variance ID:* `{variance_data.get('variance_id', 'Unknown')}`"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Action Required:* Investigation needed. <!channel>"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_This is an automated alert from the Cash Completeness Monitor. Only new variances are reported._"
                    }
                ]
            }
        ]
        
        # Create attachment for color coding
        attachments = [
            {
                "color": color,
                "blocks": blocks
            }
        ]
        
        # Send with simple text fallback
        fallback_text = (f"{emoji} New Cash Variance: {variance_data.get('account', 'Unknown')} - "
                        f"{variance_data.get('currency', 'USD')} {variance_data.get('delta_amount', 0):,.2f}")
        
        return self.send_message(
            text=fallback_text,
            attachments=attachments
        )
    
    def send_system_status(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a system status update."""
        
        status_emoji = "✅" if status_data.get('system_status') == 'operational' else "❌"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} Cash Monitor System Status"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{status_data.get('system_status', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Last Check:*\n{status_data.get('last_check', 'Never')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Known Variances:*\n{status_data.get('known_variances_count', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Timestamp:*\n{status_data.get('timestamp', 'Unknown')}"
                    }
                ]
            }
        ]
        
        return self.send_message(
            text=f"{status_emoji} System Status Update",
            blocks=blocks
        )
    
    def test_connection(self) -> bool:
        """Test the connection to Slack."""
        try:
            url = urljoin(self.base_url, '/auth.test')
            response = self.session.post(url)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"Slack connection test successful. Bot user: {result.get('user')}")
                return True
            else:
                logger.error(f"Slack connection test failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Slack connection test failed: {str(e)}")
            return False
    
    def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """Get information about a channel."""
        try:
            url = urljoin(self.base_url, '/conversations.info')
            response = self.session.get(url, params={'channel': channel})
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                return result.get('channel', {})
            else:
                raise Exception(f"Failed to get channel info: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Failed to get channel info: {str(e)}")
            raise