{
  "name": "Redash Multi-Query to Slack",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 9 * * *"
            }
          ]
        }
      },
      "name": "Daily at 9 AM",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "functionCode": "// Define your queries here\nconst queries = [\n  { id: 123, name: \"Daily Sales Report\" },\n  { id: 456, name: \"User Signups\" },\n  { id: 789, name: \"Revenue Dashboard\" }\n];\n\nreturn queries.map(query => ({ json: query }));"
      },
      "name": "Query List",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [440, 300]
    },
    {
      "parameters": {
        "url": "={{$node[\"Query List\"].json[\"redash_url\"]}}/api/queries/{{$node[\"Query List\"].json[\"id\"]}}/refresh",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "httpHeaderAuth",
        "options": {}
      },
      "name": "Refresh Query",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [640, 300]
    },
    {
      "parameters": {
        "amount": 5,
        "unit": "seconds"
      },
      "name": "Wait for Query",
      "type": "n8n-nodes-base.wait",
      "typeVersion": 1,
      "position": [840, 300]
    },
    {
      "parameters": {
        "url": "={{$node[\"Query List\"].json[\"redash_url\"]}}/api/jobs/{{$node[\"Refresh Query\"].json[\"job\"][\"id\"]}}",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "httpHeaderAuth"
      },
      "name": "Check Job Status",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [1040, 300]
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$node[\"Check Job Status\"].json[\"job\"][\"status\"]}}",
              "value2": 3
            }
          ]
        }
      },
      "name": "Job Complete?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [1240, 300]
    },
    {
      "parameters": {
        "url": "={{$node[\"Query List\"].json[\"redash_url\"]}}/api/query_results/{{$node[\"Check Job Status\"].json[\"job\"][\"query_result_id\"]}}",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "httpHeaderAuth"
      },
      "name": "Get Results",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [1440, 200]
    },
    {
      "parameters": {
        "channel": "#data-reports",
        "text": "📊 *{{$node[\"Query List\"].json[\"name\"]}}*\\n\\nRows: {{$node[\"Get Results\"].json[\"query_result\"][\"data\"][\"rows\"].length}}\\n\\n*Sample Data:*\\n```\\n{{JSON.stringify($node[\"Get Results\"].json[\"query_result\"][\"data\"][\"rows\"][0], null, 2)}}\\n```",
        "otherOptions": {
          "username": "n8n Redash Bot",
          "icon_emoji": ":bar_chart:"
        }
      },
      "name": "Send to Slack",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 1,
      "position": [1640, 200]
    },
    {
      "parameters": {
        "channel": "#data-reports",
        "text": "❌ Query {{$node[\"Query List\"].json[\"name\"]}} failed to complete",
        "otherOptions": {
          "username": "n8n Redash Bot",
          "icon_emoji": ":warning:"
        }
      },
      "name": "Send Error",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 1,
      "position": [1440, 400]
    }
  ],
  "connections": {
    "Daily at 9 AM": {
      "main": [
        [
          {
            "node": "Query List",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Query List": {
      "main": [
        [
          {
            "node": "Refresh Query",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Refresh Query": {
      "main": [
        [
          {
            "node": "Wait for Query",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Wait for Query": {
      "main": [
        [
          {
            "node": "Check Job Status",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Check Job Status": {
      "main": [
        [
          {
            "node": "Job Complete?",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Job Complete?": {
      "main": [
        [
          {
            "node": "Get Results",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Send Error",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Get Results": {
      "main": [
        [
          {
            "node": "Send to Slack",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}