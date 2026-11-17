import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Gemini AI Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

# Meta WhatsApp Cloud API Settings
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "clinic_bot_secret_verify_token_123").strip()

# Business Settings
CLINIC_OWNER_PHONE = os.getenv("CLINIC_OWNER_PHONE", "").strip()
CLINIC_NAME = os.getenv("CLINIC_NAME", "Sharma Health Clinic").strip()
DOCTOR_NAME = os.getenv("DOCTOR_NAME", "Dr. Sharma").strip()

# Clinic Timings & Consultation Fee info (for AI awareness)
CLINIC_HOURS = "Monday to Saturday: 10:00 AM - 2:00 PM, 5:00 PM - 8:00 PM. Sunday: Closed."
CONSULTATION_FEE = "₹300"
