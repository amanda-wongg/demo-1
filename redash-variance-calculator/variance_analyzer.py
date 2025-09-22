#!/usr/bin/env python3
"""
Redash Variance Analyzer
Fetches data from Redash, calculates variance and statistical insights,
then sends intelligent alerts to Slack based on thresholds.
"""

import requests
import json
import time
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Configuration
REDASH_URL = "https://your-redash-instance.com"
REDASH_API_KEY = "your-api-key-here"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

class RedashVarianceAnalyzer:
    def __init__(self, redash_url: str, api_key: str, slack_webhook: str):
        self.redash_url = redash_url.rstrip('/')
        self.api_key = api_key
        self.slack_webhook = slack_webhook
        self.headers = {'Authorization': f'Key {api_key}'}
    
    def run_query_with_params(self, query_id: int, parameters: Dict[str, Any]) -> List[Dict]:
        """Run a Redash query with parameters and return results"""
        print(f"🔄 Running query {query_id} with parameters: {parameters}")
        
        # Refresh query with parameters
        refresh_url = f"{self.redash_url}/api/queries/{query_id}/refresh"
        payload = {"parameters": parameters} if parameters else {}
        
        response = requests.post(refresh_url, headers=self.headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to refresh query: {response.status_code}")
        
        job = response.json()
        job_id = job['job']['id']
        
        # Poll for completion
        for _ in range(60):  # Wait up to 60 seconds
            job_url = f"{self.redash_url}/api/jobs/{job_id}"
            job_response = requests.get(job_url, headers=self.headers)
            
            if job_response.status_code == 200:
                job_data = job_response.json()
                if job_data['job']['status'] == 3:  # Completed
                    result_id = job_data['job']['query_result_id']
                    break
                elif job_data['job']['status'] == 4:  # Failed
                    raise Exception("Query execution failed")
            time.sleep(1)
        else:
            raise Exception("Query timeout")
        
        # Get results
        result_url = f"{self.redash_url}/api/query_results/{result_id}"
        result_response = requests.get(result_url, headers=self.headers)
        
        if result_response.status_code != 200:
            raise Exception("Failed to get query results")
        
        results = result_response.json()
        return results.get('query_result', {}).get('data', {}).get('rows', [])
    
    def calculate_variance_insights(self, data: List[Dict], value_column: str, 
                                  date_column: str = None) -> Dict[str, Any]:
        """Calculate comprehensive variance and statistical insights"""
        if not data:
            return {"error": "No data provided"}
        
        # Extract values
        values = []
        dates = []
        
        for row in data:
            if value_column in row and row[value_column] is not None:
                try:
                    val = float(row[value_column])
                    values.append(val)
                    if date_column and date_column in row:
                        dates.append(row[date_column])
                except (ValueError, TypeError):
                    continue
        
        if len(values) < 2:
            return {"error": "Insufficient data for variance calculation"}
        
        # Basic statistics
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)
        variance = statistics.variance(values)
        std_dev = statistics.stdev(values)
        min_val = min(values)
        max_val = max(values)
        
        # Additional insights
        coefficient_of_variation = (std_dev / mean_val) * 100 if mean_val != 0 else 0
        
        # Outlier detection (values beyond 2 standard deviations)
        outliers = [v for v in values if abs(v - mean_val) > 2 * std_dev]
        outlier_count = len(outliers)
        
        # Trend analysis (if we have dates)
        trend = "stable"
        if len(values) >= 5:
            # Simple trend detection
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)
            
            change_percent = ((second_avg - first_avg) / first_avg * 100) if first_avg != 0 else 0
            
            if change_percent > 10:
                trend = "increasing"
            elif change_percent < -10:
                trend = "decreasing"
        
        # Risk assessment
        risk_level = "low"
        if coefficient_of_variation > 50:
            risk_level = "high"
        elif coefficient_of_variation > 25:
            risk_level = "medium"
        
        return {
            "sample_size": len(values),
            "mean": round(mean_val, 2),
            "median": round(median_val, 2),
            "variance": round(variance, 2),
            "std_deviation": round(std_dev, 2),
            "min_value": round(min_val, 2),
            "max_value": round(max_val, 2),
            "coefficient_of_variation": round(coefficient_of_variation, 2),
            "outlier_count": outlier_count,
            "outliers": [round(o, 2) for o in outliers[:5]],  # Show first 5 outliers
            "trend": trend,
            "risk_level": risk_level,
            "range": round(max_val - min_val, 2)
        }
    
    def generate_variance_alert(self, query_name: str, insights: Dict[str, Any], 
                               thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """Generate alert based on variance thresholds"""
        if "error" in insights:
            return {
                "alert": True,
                "level": "error",
                "message": f"❌ Error calculating variance for {query_name}: {insights['error']}"
            }
        
        # Default thresholds
        default_thresholds = {
            "high_cv_threshold": 30.0,  # Coefficient of variation
            "outlier_threshold": 5,     # Number of outliers
            "variance_threshold": 1000  # Raw variance value
        }
        
        if thresholds:
            default_thresholds.update(thresholds)
        
        alerts = []
        alert_level = "info"
        
        # Check coefficient of variation
        if insights["coefficient_of_variation"] > default_thresholds["high_cv_threshold"]:
            alerts.append(f"🚨 High variability: {insights['coefficient_of_variation']:.1f}% CV")
            alert_level = "warning"
        
        # Check outliers
        if insights["outlier_count"] > default_thresholds["outlier_threshold"]:
            alerts.append(f"⚠️ {insights['outlier_count']} outliers detected")
            alert_level = "warning"
        
        # Check raw variance
        if insights["variance"] > default_thresholds["variance_threshold"]:
            alerts.append(f"📊 High variance: {insights['variance']:,.0f}")
            alert_level = "warning"
        
        # Check trend
        if insights["trend"] in ["increasing", "decreasing"]:
            emoji = "📈" if insights["trend"] == "increasing" else "📉"
            alerts.append(f"{emoji} Trend detected: {insights['trend']}")
        
        return {
            "alert": len(alerts) > 0,
            "level": alert_level,
            "alerts": alerts,
            "insights": insights
        }
    
    def format_slack_message(self, query_name: str, alert_data: Dict[str, Any], 
                           date_range: str = None) -> str:
        """Format variance analysis for Slack"""
        insights = alert_data["insights"]
        
        # Header
        if alert_data["alert"] and alert_data["level"] == "warning":
            header = f"⚠️ *Variance Alert: {query_name}*"
        elif alert_data["alert"] and alert_data["level"] == "error":
            header = f"❌ *Error: {query_name}*"
        else:
            header = f"📊 *Variance Report: {query_name}*"
        
        if date_range:
            header += f"\n📅 Period: {date_range}"
        
        # Error handling
        if alert_data["level"] == "error":
            return f"{header}\n{alert_data['message']}"
        
        # Main statistics
        stats_section = f"""
📈 *Key Statistics:*
• Sample Size: {insights['sample_size']:,} data points
• Average: {insights['mean']:,.2f}
• Variance: {insights['variance']:,.2f}
• Std Deviation: {insights['std_deviation']:,.2f}
• Range: {insights['min_value']:,.2f} - {insights['max_value']:,.2f}
"""
        
        # Risk assessment
        risk_emoji = {"low": "✅", "medium": "⚠️", "high": "🚨"}
        risk_section = f"""
🎯 *Risk Assessment:*
• Variability: {insights['coefficient_of_variation']:.1f}% CV {risk_emoji[insights['risk_level']]}
• Trend: {insights['trend'].title()}
• Outliers: {insights['outlier_count']} detected
"""
        
        # Alerts
        alert_section = ""
        if alert_data["alerts"]:
            alert_section = "\n🚨 *Alerts:*\n• " + "\n• ".join(alert_data["alerts"])
        
        # Outliers detail
        outlier_section = ""
        if insights["outliers"]:
            outlier_section = f"\n🔍 *Sample Outliers:* {', '.join(map(str, insights['outliers']))}"
        
        return f"{header}{stats_section}{risk_section}{alert_section}{outlier_section}"
    
    def send_to_slack(self, message: str) -> bool:
        """Send message to Slack"""
        payload = {
            "text": message,
            "username": "Variance Analyzer",
            "icon_emoji": ":chart_with_upwards_trend:"
        }
        
        response = requests.post(self.slack_webhook, json=payload)
        return response.status_code == 200
    
    def analyze_and_alert(self, query_id: int, query_name: str, value_column: str,
                         start_date: str, end_date: str, date_column: str = None,
                         thresholds: Dict[str, float] = None) -> bool:
        """Complete analysis workflow"""
        try:
            # Prepare parameters
            parameters = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            # Get data
            data = self.run_query_with_params(query_id, parameters)
            print(f"📊 Retrieved {len(data)} rows")
            
            # Calculate variance
            insights = self.calculate_variance_insights(data, value_column, date_column)
            print(f"📈 Calculated insights: CV = {insights.get('coefficient_of_variation', 'N/A')}%")
            
            # Generate alert
            alert_data = self.generate_variance_alert(query_name, insights, thresholds)
            
            # Format message
            date_range = f"{start_date} to {end_date}"
            message = self.format_slack_message(query_name, alert_data, date_range)
            
            # Send to Slack
            if self.send_to_slack(message):
                print("✅ Sent to Slack successfully")
                return True
            else:
                print("❌ Failed to send to Slack")
                return False
                
        except Exception as e:
            error_message = f"❌ *Error analyzing {query_name}*\n```{str(e)}```"
            self.send_to_slack(error_message)
            print(f"❌ Error: {e}")
            return False

def main():
    """Example usage"""
    analyzer = RedashVarianceAnalyzer(REDASH_URL, REDASH_API_KEY, SLACK_WEBHOOK_URL)
    
    # Define your analysis jobs
    analysis_jobs = [
        {
            "query_id": 123,
            "query_name": "Daily Sales Variance",
            "value_column": "sales_amount",  # Column containing the values to analyze
            "date_column": "sale_date",      # Optional: for trend analysis
            "thresholds": {
                "high_cv_threshold": 25.0,   # Alert if CV > 25%
                "outlier_threshold": 3,      # Alert if > 3 outliers
                "variance_threshold": 500    # Alert if variance > 500
            }
        },
        {
            "query_id": 456,
            "query_name": "User Signup Variance",
            "value_column": "signup_count",
            "thresholds": {
                "high_cv_threshold": 40.0,
                "outlier_threshold": 2
            }
        }
    ]
    
    # Date range - you can make this dynamic
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"🚀 Starting variance analysis for period: {start_date} to {end_date}")
    
    success_count = 0
    for job in analysis_jobs:
        print(f"\n📊 Analyzing: {job['query_name']}")
        
        if analyzer.analyze_and_alert(
            query_id=job["query_id"],
            query_name=job["query_name"],
            value_column=job["value_column"],
            start_date=start_date,
            end_date=end_date,
            date_column=job.get("date_column"),
            thresholds=job.get("thresholds")
        ):
            success_count += 1
        
        time.sleep(2)  # Be nice to the API
    
    print(f"\n🎉 Completed: {success_count}/{len(analysis_jobs)} analyses successful")

if __name__ == "__main__":
    main()