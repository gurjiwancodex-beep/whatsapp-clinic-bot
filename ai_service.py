import logging
from typing import Optional
from google import genai
from google.genai import types

import config
import database
import appointment_service
import whatsapp_service
import clinic_manager

logger = logging.getLogger(__name__)

def get_system_prompt() -> str:
    """
    Builds the system prompt dynamically using the latest live clinic info
    (updated from Google Sheets or Mobile Admin).
    """
    info = clinic_manager.get_current_clinic_info()
    
    leave_notice = (
        "⚠️ CRITICAL ALERT: Doctor is ON LEAVE today! Do NOT schedule appointments for today. "
        "Politely inform patients that the doctor is on leave today, but you can book them for tomorrow or upcoming days."
        if info.get("is_doctor_on_leave")
        else "Doctor is in clinic and available today."
    )

    return f"""
You are the warm, empathetic, and professional AI Assistant / Receptionist for {info['clinic_name']} (Doctor: {info['doctor_name']}).
Your goal is to answer patient inquiries politely and help them schedule an in-clinic doctor appointment.

LIVE CLINIC INFORMATION (DYNAMICALLY UPDATED):
- Clinic Name: {info['clinic_name']}
- Doctor: {info['doctor_name']}
- Timings: {info['clinic_hours']}
- Consultation Fee: {info['consultation_fee']}
- Services: {info.get('services', 'General Consultation')}
- Today's Special Notice / News: {info.get('today_notice', 'None')}
- Doctor Status Today: {leave_notice}

MULTILINGUAL COMMUNICATION (STRICT):
1. Detect the user's language and reply in the EXACT same language and script:
   - If user speaks Punjabi in Roman/English script (e.g. "Doctor saab nu milna si", "kal 4 vaje aa sakda?"), reply in warm Roman Punjabi (e.g. "Sat Sri Akal ji! Hanji, Dr. Sharma ji...").
   - If user writes in Gurmukhi script (e.g. "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ"), reply in Gurmukhi Punjabi.
   - If user speaks Hindi (Devanagari or Roman Hindi), reply in Hindi.
   - If user speaks English, reply in English.
2. WhatsApp formatting: Keep replies concise, polite, and human-like. Use emojis (🙏, 🏥, 🩺, 📅). Avoid giant walls of text.

APPOINTMENT BOOKING PROCESS:
To book an appointment, collect:
1. Patient's Full Name
2. Preferred Date & Time (check if it falls within clinic hours and doctor is not on leave)
3. Brief reason / problem (e.g., fever, regular checkup, knee pain)

If any detail is missing, ask for it nicely.
As soon as the user provides or confirms all details, IMMEDIATELY call the `book_appointment` tool to finalize the booking.
After calling the tool, confirm the booking warmly with the patient.
"""

def get_gemini_client() -> Optional[genai.Client]:
    if not config.GEMINI_API_KEY:
        return None
    return genai.Client(api_key=config.GEMINI_API_KEY)

async def generate_bot_reply(sender_id: str, incoming_text: str) -> str:
    """
    Handles user message, maintains context history, executes tool call if appointment is booked,
    and returns the AI assistant response.
    """
    client = get_gemini_client()
    if not client:
        return (
            "⚠️ [Demo Mode - API Key Missing]\n"
            "Please set your `GEMINI_API_KEY` in the `.env` file to enable AI responses.\n"
            f"Received: '{incoming_text}' from {sender_id}."
        )

    # Tool definition for appointment booking
    booking_context = {"booked": False, "data": None}

    def book_appointment(
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        reason: str = "General Consultation"
    ) -> str:
        """Books an appointment for the patient and saves it to the clinic system.
        
        Args:
            patient_name: Full name of the patient.
            appointment_date: Date of appointment (e.g., 'Tomorrow' or '2026-11-18').
            appointment_time: Time of appointment (e.g., '4:00 PM').
            reason: Reason for visit or symptoms.
        """
        booking_result = appointment_service.process_booking(
            patient_name=patient_name,
            patient_phone=sender_id,
            reason=reason,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        )
        booking_context["booked"] = True
        booking_context["data"] = booking_result
        return f"SUCCESS: Appointment #{booking_result['appointment_id']} confirmed for {patient_name} on {appointment_date} at {appointment_time}."

    # Retrieve past conversation history from SQLite
    history_records = database.get_conversation_history(sender_id, limit=6)
    
    # Construct history array for Gemini Chat
    history = []
    for item in history_records:
        role = "user" if item["role"] == "user" else "model"
        history.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=item["content"])]
        ))

    try:
        # Build prompt dynamically with live clinic info (leaves, notices, fees)
        dynamic_system_prompt = get_system_prompt()

        chat = client.chats.create(
            model=config.GEMINI_MODEL,
            history=history,
            config=types.GenerateContentConfig(
                system_instruction=dynamic_system_prompt,
                tools=[book_appointment],
                temperature=0.7,
            )
        )
        
        response = chat.send_message(incoming_text)
        reply_text = response.text or ""

        # If a booking occurred during tool execution, send the instant owner WhatsApp alert!
        if booking_context["booked"] and booking_context["data"]:
            alert_msg = booking_context["data"]["owner_alert_message"]
            await whatsapp_service.notify_owner_new_booking(alert_msg)

        return reply_text.strip()

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        return f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! ਮੈਂ ਤੁਹਾਡਾ ਸੁਨੇਹਾ ਪ੍ਰਾਪਤ ਕਰ ਲਿਆ ਹੈ। (Error: {str(e)})"
