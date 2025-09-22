# Complete n8n Setup Guide: Redash to Slack

n8n is a visual workflow automation tool - think of it as a free, self-hosted alternative to Zapier. Perfect for connecting Redash and Slack without coding!

## Part 1: Install n8n (5 minutes)

### Option A: Docker (Recommended)
```bash
# Pull and run n8n
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n

# Or with persistence:
docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
```

### Option B: npm
```bash
# Install n8n globally
npm install n8n -g

# Run n8n
n8n start
```

### Option C: Cloud (Easiest)
1. Go to https://n8n.cloud
2. Sign up for free account (5 workflows, 2,500 executions/month)
3. Skip to Part 2

**Access n8n:** Open http://localhost:5678 in your browser

## Part 2: Setup Credentials (3 minutes)

### 2.1 Redash API Credential
1. In n8n, go to **Settings** → **Credentials**
2. Click **"+ Add Credential"**
3. Search for **"HTTP Header Auth"**
4. Configure:
   - **Name**: `Redash API`
   - **Header Name**: `Authorization`
   - **Header Value**: `Key YOUR_REDASH_API_KEY`
5. Click **Save**

### 2.2 Slack Credential
1. Click **"+ Add Credential"** again
2. Search for **"Slack"**
3. Choose **"Slack OAuth2 API"**
4. Click **"Connect my account"**
5. Authorize n8n to access your Slack workspace
6. Click **Save**

## Part 3: Create the Workflow (10 minutes)

### 3.1 Start New Workflow
1. Click **"+ Add workflow"**
2. Give it a name: `Redash to Slack Reports`

### 3.2 Add Trigger Node
1. Click the **"+"** button
2. Search for **"Cron"**
3. Configure:
   - **Mode**: Expression
   - **Expression**: `0 9 * * *` (daily at 9 AM)
   - Or use the visual editor for different schedules

### 3.3 Add Function Node (Query List)
1. Connect to Cron → Click **"+"** 
2. Search for **"Function"**
3. Replace the code with:

```javascript
// 🔧 Configure your queries here
const REDASH_URL = "https://your-redash-instance.com";  // ← Change this
const queries = [
  { id: 123, name: "Daily Sales Report" },              // ← Your query IDs
  { id: 456, name: "Weekly User Signups" },
  { id: 789, name: "Revenue Dashboard" }
];

// Return each query as separate item for processing
return queries.map(query => ({ 
  json: { 
    ...query, 
    redash_url: REDASH_URL 
  } 
}));
```

### 3.4 Add HTTP Request Node (Refresh Query)
1. Connect Function → Click **"+"**
2. Search for **"HTTP Request"**
3. Configure:
   - **Method**: POST
   - **URL**: `={{$json.redash_url}}/api/queries/{{$json.id}}/refresh`
   - **Authentication**: Use existing credential → `Redash API`

### 3.5 Add Wait Node
1. Connect HTTP Request → Click **"+"**
2. Search for **"Wait"**
3. Configure:
   - **Amount**: 5
   - **Unit**: seconds

### 3.6 Add HTTP Request Node (Check Status)
1. Connect Wait → Click **"+"**
2. Search for **"HTTP Request"**
3. Configure:
   - **Method**: GET
   - **URL**: `={{$json.redash_url}}/api/jobs/{{$node["HTTP Request"].json.job.id}}`
   - **Authentication**: Use existing credential → `Redash API`

### 3.7 Add IF Node (Check Completion)
1. Connect HTTP Request → Click **"+"**
2. Search for **"IF"**
3. Configure:
   - **Condition**: Number
   - **Value 1**: `={{$json.job.status}}`
   - **Operation**: Equal
   - **Value 2**: `3` (completed status)

### 3.8 Add HTTP Request Node (Get Results) - TRUE branch
1. Connect IF (true) → Click **"+"**
2. Search for **"HTTP Request"**
3. Configure:
   - **Method**: GET
   - **URL**: `={{$json.redash_url}}/api/query_results/{{$json.job.query_result_id}}`
   - **Authentication**: Use existing credential → `Redash API`

### 3.9 Add Slack Node (Send Results) - Connect to Get Results
1. Connect HTTP Request → Click **"+"**
2. Search for **"Slack"**
3. Configure:
   - **Resource**: Message
   - **Operation**: Post
   - **Authentication**: Use your Slack credential
   - **Channel**: `#data-reports` (or your channel)
   - **Text**: 
```
📊 *{{$node["Function"].json.name}}*

📈 Rows returned: {{$json.query_result.data.rows.length}}
🔗 View in Redash: {{$node["Function"].json.redash_url}}/queries/{{$node["Function"].json.id}}

*Sample data:*
```
{{JSON.stringify($json.query_result.data.rows[0], null, 2)}}
```
```

### 3.10 Add Slack Node (Send Error) - FALSE branch
1. Connect IF (false) → Click **"+"**
2. Search for **"Slack"**
3. Configure:
   - **Channel**: `#data-reports`
   - **Text**: `❌ Query {{$node["Function"].json.name}} failed or timed out`

## Part 4: Test and Activate (2 minutes)

### 4.1 Test the Workflow
1. Click **"Execute Workflow"** button (top right)
2. Watch each node execute
3. Check your Slack channel for messages
4. Debug any red (failed) nodes

### 4.2 Activate the Workflow
1. Toggle **"Active"** switch (top right)
2. Your workflow will now run automatically on schedule!

## Part 5: Advanced Customizations

### 5.1 Multiple Schedules
Create separate workflows for different schedules:
- **Daily reports**: `0 9 * * *` (9 AM daily)
- **Weekly reports**: `0 9 * * 1` (9 AM Mondays)
- **Monthly reports**: `0 9 1 * *` (9 AM, 1st of month)

### 5.2 Better Error Handling
Add a **Switch** node after "Check Status" to handle different job statuses:
- Status 3: Success → Get Results
- Status 4: Failed → Send Error
- Other: Still running → Wait longer or timeout

### 5.3 Rich Slack Messages
Replace the simple text with Slack Block Kit for better formatting:

```javascript
// In Slack node, use "Blocks" instead of "Text"
[
  {
    "type": "header",
    "text": {
      "type": "plain_text",
      "text": `📊 ${$node["Function"].json.name}`
    }
  },
  {
    "type": "section",
    "fields": [
      {
        "type": "mrkdwn",
        "text": `*Rows:* ${$json.query_result.data.rows.length}`
      },
      {
        "type": "mrkdwn",
        "text": `*Updated:* ${new Date().toLocaleString()}`
      }
    ]
  },
  {
    "type": "section",
    "text": {
      "type": "mrkdwn",
      "text": `<${$node["Function"].json.redash_url}/queries/${$node["Function"].json.id}|View in Redash>`
    }
  }
]
```

### 5.4 Conditional Reports
Add an **IF** node after "Get Results" to only send reports when certain conditions are met:
- Only send if row count > 0
- Only send if values exceed thresholds
- Only send on weekdays

## Troubleshooting

### ❌ "Unauthorized" errors
- Check your Redash API key in credentials
- Verify the API key has permission to run queries

### ❌ Slack messages not sending
- Re-authenticate your Slack credential
- Check channel name (use # prefix)
- Verify the bot has permission to post in the channel

### ❌ Queries timing out
- Increase wait time or add retry logic
- Optimize your Redash queries
- Add multiple wait/check cycles

### ❌ n8n workflow not triggering
- Check the cron expression is correct
- Ensure workflow is **Active** (toggle switch)
- Check n8n logs for errors

## 🎉 You're Done!

**What you've built:**
- ✅ Visual, no-code workflow automation
- ✅ Automatic Redash query execution
- ✅ Formatted Slack notifications
- ✅ Error handling and monitoring
- ✅ Flexible scheduling

**Next Steps:**
- Add more queries to the Function node
- Create different workflows for different teams
- Set up alerts based on data conditions
- Export/backup your workflows

**Pro Tips:**
- Use n8n's built-in error workflow for monitoring
- Set up webhooks for on-demand execution
- Use environment variables for sensitive data
- Create templates for common patterns