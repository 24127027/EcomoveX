# 🔑 How to Get Climatiq API Key (FREE)

## Step 1: Sign Up

1. Go to: **https://www.climatiq.io/**
2. Click **"Get Started"** or **"Sign Up"**
3. Fill in:
   - Email address
   - Password
   - Company name (có thể để tên project: "EcomoveX")
4. Click **"Create Account"**

## Step 2: Verify Email

1. Check your email inbox
2. Click verification link
3. You'll be redirected to Climatiq dashboard

## Step 3: Get API Key

1. After login, you'll see the **Dashboard**
2. Look for **"API Keys"** section (usually on left sidebar or top menu)
3. Click **"Create API Key"** or you'll see default key already created
4. Copy the API key (format: `xxx...`)

## Step 4: Add to .env File

1. Open: `backend/.env`
2. Add this line:
   ```env
   CLIMATIQ_API_KEY=your_api_key_here
   ```
3. Save file

## Free Tier Details

- ✅ **5,000 requests/month** (FREE forever)
- ✅ No credit card required
- ✅ Access to full database
- ✅ All transport emission factors included

## Example:

```env
# Your .env file should look like this:
DB_HOST=localhost
...
CLIMATIQ_API_KEY=sk_1234567890abcdef...
```

## Test Your API Key

Run this command:
```bash
python tests/test_climatiq_integration.py
```

Expected output:
```
✅ API Key found: sk_...
🔍 SEARCHING CLIMATIQ DATABASE:
✅ Found results
```

## Troubleshooting

### ❌ "Invalid API key"
- Make sure you copied the full key
- Check for extra spaces
- Key format should be: `sk_...`

### ❌ "CLIMATIQ_API_KEY not found"
- Make sure .env file is in `backend/` folder
- Restart your application after adding the key

### ❌ "Rate limit exceeded"
- Free tier: 5,000/month
- With 24h cache: only ~30 requests/month needed
- Check if you're calling API too frequently

## Need Help?

- Climatiq Docs: https://www.climatiq.io/docs
- API Reference: https://www.climatiq.io/docs/api-reference
- Support: support@climatiq.io
