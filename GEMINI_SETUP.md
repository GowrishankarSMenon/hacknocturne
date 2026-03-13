# GhostNet - Gemini API Configuration

**Status:** ✅ Fully Configured for Google Gemini API  
**Date:** January 28, 2026  
**API:** Google Gemini Pro (gemini-pro)

---

## What Was Changed

### 1. **Dependencies Updated** (requirements.txt)
```diff
- openai==1.3.5
- langgraph==0.0.47
- langchain-openai==0.0.5

+ google-generativeai==0.3.0
+ langchain-google-genai==0.0.5
```

### 2. **API Key Configuration** (.env & .env.example)
```diff
- OPENAI_API_KEY=sk-your-key-here
+ GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. **Agent Code** (agents/os_simulator.py)
- Updated `OSSimulator` class to use `google.generativeai` library
- Updated `Orchestrator` class for Gemini API
- Updated `Profiler` class for Gemini API
- Changed model from `gpt-4o-mini` to `gemini-pro`

### 4. **Main Entry Point** (main.py)
- Updated API key validation to check for `GEMINI_API_KEY`

### 5. **Documentation** (README, QUICKSTART)
- Updated all references from OpenAI to Google Gemini
- Updated API key retrieval link

---

## Files Modified

| File | Changes |
|------|---------|
| `requirements.txt` | Replaced OpenAI with google-generativeai |
| `.env.example` | Changed to GEMINI_API_KEY |
| `.env` | Created with Gemini config (ready to use!) |
| `agents/os_simulator.py` | All 3 classes updated to use Gemini API |
| `main.py` | Updated API key check |
| `README.md` | Updated tech stack & env vars |
| `QUICKSTART.md` | Updated API setup instructions |

---

## Setup Instructions

### 1. Install Updated Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Your Gemini API Key

Go to: **https://ai.google.dev/**

- Click "Get API Key"
- Select or create a Google Cloud project
- Copy the API key

### 3. Configure .env File

The `.env` file has already been created for you:

```bash
# .env (already created in ghostnet folder)
GEMINI_API_KEY=your-gemini-api-key-here
```

Just replace `your-gemini-api-key-here` with your actual Gemini API key.

### 4. Verify Installation
```bash
python test_components.py
```

---

## How Gemini API is Used

### OSSimulator
- **Model:** `gemini-pro`
- **Purpose:** Generate realistic terminal output
- **Temperature:** 0.7 (creative but consistent)
- **Max Tokens:** 500

### Orchestrator
- **Model:** `gemini-pro`
- **Purpose:** Analyze attacker intent
- **Temperature:** 0.5 (balanced)
- **Max Tokens:** 200

### Profiler
- **Model:** `gemini-pro`
- **Purpose:** Assess attacker skill level
- **Temperature:** 0.5 (balanced)
- **Max Tokens:** 200

---

## Advantages of Using Gemini API

✅ **Free Tier Available**
- Unlimited requests (with daily limits)
- No credit card required
- Generous free quota

✅ **Fast Responses**
- ~1-2 seconds per request
- Good enough for honeypot use

✅ **Easy Integration**
- Simple library (`google-generativeai`)
- Straightforward API design
- Good error handling

✅ **Reliable**
- Backed by Google
- Stable API endpoints
- Good documentation

---

## Cost Comparison

| Provider | Cost | Speed | Free Tier |
|----------|------|-------|-----------|
| **OpenAI (GPT-4o-mini)** | $0.00015/1K tokens | ~100ms | No |
| **Google Gemini (Free)** | FREE | ~1-2s | Yes ✅ |
| **Google Gemini (Paid)** | Variable | ~1-2s | Yes |

**For GhostNet:** Gemini free tier is perfect! No costs, unlimited testing.

---

## Running GhostNet with Gemini

### Terminal 1: Start Honeypot
```bash
python main.py
```

Expected output:
```
🎭 GhostNet is now running...
📡 SSH Server listening on 0.0.0.0:2222
🚀 Waiting for attackers...
```

### Terminal 2: Start Dashboard
```bash
streamlit run dashboard/app.py
```

### Terminal 3: Test Connection
```bash
ssh user@localhost -p 2222
# Password: (anything works)
> whoami
> ls
> pwd
```

---

## Troubleshooting

### "GEMINI_API_KEY not set"
```bash
# Verify .env exists
ls -la .env

# Check the key is there
grep GEMINI_API_KEY .env

# Make sure you've replaced the placeholder value
```

### "Permission denied" from Gemini API
- Check your API key is valid
- Verify it's not expired
- Make sure you have the correct project selected

### "Rate limit exceeded"
- Gemini free tier has daily limits
- Wait 24 hours or upgrade to paid plan
- Limits are very generous for typical use

### Slow Responses
- Normal! Gemini takes 1-2 seconds
- OpenAI took ~100ms by comparison
- But Gemini is free, so trade-off worth it

---

## Quick Reference

| Item | Value |
|------|-------|
| **API Provider** | Google Gemini |
| **Model** | gemini-pro |
| **Library** | google-generativeai==0.3.0 |
| **API Key Env Var** | `GEMINI_API_KEY` |
| **Free Tier** | Yes ✅ |
| **Setup Time** | < 5 minutes |

---

## File Locations

- **Configuration:** `d:\just learning\ghostnet\.env` ← **Edit this file!**
- **Dependencies:** `d:\just learning\ghostnet\requirements.txt`
- **API Code:** `d:\just learning\ghostnet\agents\os_simulator.py`

---

## Next Steps

1. **Edit .env file:**
   ```bash
   # Replace: GEMINI_API_KEY=your-gemini-api-key-here
   # With your actual Gemini API key from https://ai.google.dev/
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test installation:**
   ```bash
   python test_components.py
   ```

4. **Run the honeypot:**
   ```bash
   python main.py
   ```

---

## Summary

✅ All files updated to use Google Gemini API  
✅ `.env` file created and ready to configure  
✅ Dependencies updated in `requirements.txt`  
✅ Documentation updated  
✅ Ready to run with free Gemini tier  

**Just add your Gemini API key to `.env` and you're good to go!**

---

**Gemini Configuration Complete!**  
Get your API key: https://ai.google.dev/
