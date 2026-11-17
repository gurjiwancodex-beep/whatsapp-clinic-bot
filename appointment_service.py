import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional
import database
import config

def generate_google_calendar_link(title: str, details: str, date_str: str, time_str: str) -> str:
    """
    Generates a 1-click Google Calendar URL to add the appointment directly.
    Example date_str: '2026-11-18', time_str: '16:00'
    """
    try:
        # Simple fallback URL builder
        base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
        params = {
            "text": title,
            "details": details,
            "location": config.CLINIC_NAME,
        }
        return f"{base}&{urllib.parse.urlencode(params)}"
    except Exception:
        return "https://calendar.google.com"

def process_booking(
    patient_name: str,
    patient_phone: str,
    reason: str,
    appointment_date: str,
    appointment_time: str
) -> Dict[str, Any]:
    """
    Saves booking to local SQLite database and prepares notifications.
    """
    # 1. Save in database
    appointment_id = database.create_appointment(
        patient_name=patient_name,
        patient_phone=patient_phone,
        reason=reason,
        appointment_date=appointment_date,
        appointment_time=appointment_time
    )

    # 2. Generate Calendar Link
    calendar_link = generate_google_calendar_link(
        title=f"Doctor Appointment - {patient_name}",
        details=f"Patient: {patient_name}\nPhone: {patient_phone}\nReason: {reason}\nDoctor: {config.DOCTOR_NAME}",
        date_str=appointment_date,
        time_str=appointment_time
    )

    # 3. Format Owner WhatsApp Alert
    owner_alert_message = (
        f"🚨 *ਨਵੀਂ ਅਪਾਇੰਟਮੈਂਟ ਬੁੱਕ ਹੋਈ ਹੈ (New Appointment)* 🚨\n\n"
        f"👤 *ਮਰੀਜ਼ ਦਾ ਨਾਮ:* {patient_name}\n"
        f"📞 *ਫ਼ੋਨ ਨੰਬਰ:* {patient_phone}\n"
        f"📅 *ਤਾਰੀਖ:* {appointment_date}\n"
        f"⏰ *ਸਮਾਂ:* {appointment_time}\n"
        f"🩺 *ਸਮੱਸਿਆ / ਮਕਸਦ:* {reason or 'General Consultation'}\n"
        f"🆔 *ਬੁਕਿੰਗ ਆਈਡੀ:* #{appointment_id}\n\n"
        f"🏥 *ਕਲੀਨਿਕ:* {config.CLINIC_NAME}"
    )

    return {
        "appointment_id": appointment_id,
        "patient_name": patient_name,
        "patient_phone": patient_phone,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "reason": reason,
        "calendar_link": calendar_link,
        "owner_alert_message": owner_alert_message
    }
