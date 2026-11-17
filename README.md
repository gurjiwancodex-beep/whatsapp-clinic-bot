# 🏥 Multilingual WhatsApp AI Appointment Bot for Clinics & Businesses

A complete, production-ready, ₹0-budget WhatsApp AI Receptionist & Appointment Booking System built with:
- **Google Gemini API** (`google-genai` SDK) for multilingual conversation (Punjabi, Hindi, English).
- **Meta WhatsApp Cloud API** (Free Developer Tier) for WhatsApp messaging.
- **FastAPI** Python backend for Webhook handling and appointment workflow.
- **SQLite Database** (`clinic_bot.db`) for storing conversations and bookings.
- **Instant Owner Alerts** via WhatsApp whenever an appointment is confirmed.

---

## 📁 Project Structure

```
whatsapp-clinic-bot/
├── .env.example              # Template for environment variables
├── .env                      # Your local secret keys
├── requirements.txt          # Python dependencies
├── config.py                 # Configuration loader
├── database.py               # SQLite database & chat history management
├── ai_service.py             # Multilingual Gemini AI agent with booking tool
├── appointment_service.py    # Appointment logic & calendar link generation
├── whatsapp_service.py       # WhatsApp Cloud API messaging & owner notifications
├── main.py                   # FastAPI server & WhatsApp Webhook listener
└── test_simulation.py        # Terminal chat simulator (test without WhatsApp)
```

---

## 🚀 Step 1: Get Your Free Gemini API Key (Takes 1 Minute)

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **"Get API key"** -> **"Create API key"**.
4. Copy the API key and paste it into `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   ```

---

## 🧪 Step 2: Test Locally in Terminal (Instant Verification)

You don't even need WhatsApp configured to test the AI brain and appointment logic right now!

Open your terminal in this directory:
```bash
cd E:\whatsapp-clinic-bot
.\.venv\Scripts\activate
python test_simulation.py
```

Try chatting with the bot:
- *"Sat Sri Akal ji, doctor saab nu milna si"*
- *"Haanji, bukhar hai 2 din ton"*
- *"Mera naam Gurpreet Singh hai, kal dupehre 3 vaje slot de do"*

Watch the bot understand, extract the appointment details, save them to the database, and trigger the owner notification format!

---

## 📱 Step 3: Set Up Meta WhatsApp Cloud API (Free Developer Account)

1. Go to [Meta for Developers](https://developers.facebook.com/).
2. Log in with your Facebook account and click **"My Apps"** -> **"Create App"**.
3. Select **"Other"** -> Click **Next** -> Select Type: **"Business"** -> Give it a name (e.g. `Clinic Bot`).
4. On the App Dashboard, find **"WhatsApp"** and click **"Set Up"**.
5. You will be redirected to the **WhatsApp > API Setup** page:
   - You will see a **Temporary Access Token** (valid for 24 hours, perfect for testing).
   - You will see a **Phone Number ID**.
   - You will see a **Test WhatsApp Number** provided by Meta.
   - In Step 2 on that page ("Send and receive messages"), add your personal phone number as a **Recipient Phone Number** (Meta will send a 6-digit verification code to your WhatsApp to verify it).
6. Copy the values into your `.env` file:
   ```env
   WHATSAPP_TOKEN=EAAG...your_token...
   WHATSAPP_PHONE_NUMBER_ID=123456789012345
   CLINIC_OWNER_PHONE=919876543210
   ```

---

## 🌐 Step 4: Expose Localhost to Internet (Free with ngrok or Cloudflare Tunnel)

Meta needs a publicly accessible HTTPS URL to send WhatsApp webhook messages.

### Option A: Using ngrok (Recommended)
Download ngrok from [ngrok.com](https://ngrok.com/) or run:
```bash
winget install ngrok.ngrok
```
Then start the tunnel:
```bash
ngrok http 8000
```
Copy the `https://xxxx.ngrok-free.app` forwarding address.

### Option B: Using Cloudflare Tunnel (cloudflared)
```bash
winget install Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8000
```
Copy the `https://xxxx.trycloudflare.com` URL.

---

## ⚙️ Step 5: Configure Webhook in Meta Dashboard

1. In your Meta Developer Dashboard, click on **WhatsApp** -> **Configuration** in the left sidebar.
2. In the **Webhook** section, click **Edit**:
   - **Callback URL:** `https://your-tunnel-url.ngrok-free.app/webhook`
   - **Verify Token:** `clinic_bot_secret_verify_token_123` (matching the one in your `.env`)
3. Click **"Verify and Save"**. (Ensure your FastAPI server is running first!).
4. Under **Webhook fields**, click **Manage** and check the box for **`messages`**, then click **Done**.

---

## ▶️ Step 6: Start the Server

```bash
.\.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Now, take your mobile phone and send a message on WhatsApp to the Meta Test Number:
> *"Doctor saab nu milna si"*

The bot will reply on WhatsApp in Punjabi/Hindi/English, guide the patient, book the slot, and send an instant notification to the clinic owner's WhatsApp!

You can also view all booked appointments live in your browser at:
`http://localhost:8000/appointments`
