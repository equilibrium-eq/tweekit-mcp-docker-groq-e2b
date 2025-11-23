# Discord Error Reporting Setup

The demo application includes opt-in error reporting to Discord webhooks for development team monitoring.

## Features

When enabled, the system will automatically report file conversion errors to your Discord channel with:
- Filename and file extension
- User-friendly error message
- Technical error details (traceback)
- Timestamp

## Setup Instructions

### 1. Create a Discord Webhook

1. Open Discord and navigate to your server
2. Go to Server Settings → Integrations
3. Click "Create Webhook" or select existing webhook
4. Choose the channel where you want error reports
5. Copy the Webhook URL (looks like `https://discord.com/api/webhooks/...`)

### 2. Configure Environment Variables

Add these to your `.envrc` file (or export directly):

```bash
# Discord Error Reporting (Optional)
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
export ERROR_REPORTING_ENABLED="true"
```

### 3. Reload Environment

```bash
source .envrc
```

### 4. Restart the Demo Server

```bash
cd demo
python3 api.py
```

## How It Works

### Format Fallback Strategy

The system automatically tries to convert text-like files (`.md`, `.readme`, `.log`, etc.) to `.txt` format if the original conversion fails. This prevents errors on unrecognized text formats.

Text-like extensions that trigger fallback:
- Documentation: `readme`, `md`, `markdown`, `rst`, `textile`, `org`
- Config files: `log`, `conf`, `config`, `cfg`, `ini`, `yaml`, `yml`
- Data files: `json`, `xml`, `csv`, `tsv`, `sql`
- Scripts: `sh`, `bash`, `zsh`

### Error Display

Users see a clean, friendly error message:
```
❌ File type '.xyz' is not currently supported
```

With expandable technical details:
```
Technical Details ▸
  [Full traceback and error details]
```

### Discord Notifications

When `ERROR_REPORTING_ENABLED=true`, errors are sent to Discord with:

```
⚠️ TweekIT Conversion Error
Filename: document.xyz
Extension: .xyz
Error: File type '.xyz' is not currently supported
Details: [Truncated traceback]
```

## Security Notes

- Discord webhook URL contains secrets - never commit to version control
- Error reporting is opt-in (disabled by default)
- Details are truncated to 1500 characters to fit Discord limits
- Only conversion errors are reported, not successful operations
- No sensitive file content is transmitted

## Deployment

### Docker/Cloud Run

Set environment variables in your deployment:

```bash
gcloud run services update tweekit-mcp \
  --set-env-vars="DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/..." \
  --set-env-vars="ERROR_REPORTING_ENABLED=true"
```

### Local Development

```bash
# In .envrc
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export ERROR_REPORTING_ENABLED="true"
```

### Testing

To test error reporting, try uploading a truly unsupported binary format (not a text-like format):

```bash
# Create a test file with unsupported format
echo "test" > test.unsupported
# Upload via demo UI at http://localhost:8081
```

You should see:
1. User-friendly error in UI with expandable details
2. Discord notification in your configured channel (if enabled)

## Disabling Error Reporting

To disable:

```bash
export ERROR_REPORTING_ENABLED="false"
# or just remove the environment variable
```

Error reporting will be disabled by default if `ERROR_REPORTING_ENABLED` is not set or `DISCORD_WEBHOOK_URL` is missing.

## Support

For issues with Discord webhook setup:
- Verify webhook URL is correct
- Check channel permissions
- Ensure webhook hasn't been deleted
- Check server logs for "Failed to report error to Discord" messages
