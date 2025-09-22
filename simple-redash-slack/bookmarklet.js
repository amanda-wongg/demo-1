// Redash to Slack Bookmarklet
// 1. Create a bookmark in your browser
// 2. Set URL to: javascript:(function(){/* PASTE CODE BELOW */})();
// 3. Click bookmark when viewing Redash query results

javascript:(function(){
    // Configuration - change these
    var slackWebhook = 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK';
    
    // Get query info from current page
    var queryName = document.querySelector('h3')?.textContent || 'Redash Query';
    var currentUrl = window.location.href;
    
    // Try to get table data
    var tableRows = document.querySelectorAll('table tbody tr');
    var dataPreview = '';
    
    if (tableRows.length > 0) {
        dataPreview = `Found ${tableRows.length} rows of data`;
        
        // Get first few rows as preview
        for (let i = 0; i < Math.min(3, tableRows.length); i++) {
            var cells = tableRows[i].querySelectorAll('td');
            var rowData = Array.from(cells).map(cell => cell.textContent.trim()).join(' | ');
            dataPreview += `\nRow ${i+1}: ${rowData}`;
        }
    } else {
        dataPreview = 'No table data found on this page';
    }
    
    // Create Slack message
    var message = `📊 *${queryName}*\n${dataPreview}\n\n🔗 View in Redash: ${currentUrl}`;
    
    // Send to Slack
    fetch(slackWebhook, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            text: message,
            username: 'Redash Bookmarklet',
            icon_emoji: ':bar_chart:'
        })
    }).then(response => {
        if (response.ok) {
            alert('✅ Sent to Slack!');
        } else {
            alert('❌ Failed to send to Slack');
        }
    }).catch(error => {
        alert('❌ Error: ' + error.message);
    });
})();