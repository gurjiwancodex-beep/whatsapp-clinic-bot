import httpx
import logging
from typing import Optional
import config

logger = logging.getLogger(__name__)

async def send_whatsapp_message(to_phone: str, text: str) -> bool:
    """
    Sends a WhatsApp message via official Meta WhatsApp Cloud API.
    to_phone: E.164 format without '+' or spaces, e.g. '919876543210'
    """
    # Clean phone number (strip '+', spaces, dashes)
    clean_phone = "".join(filter(str.isdigit, to_phone))
    
    if not config.WHATSAPP_TOKEN or not config.WHATSAPP_PHONE_NUMBER_ID:
        logger.warning(
            f"[WhatsApp Mock Mode] No Token/PhoneID configured. Message to {clean_phone}:\n{text}"
        )
        print(f"\n================ [WHATSAPP MESSAGE TO {clean_phone}] ================\n{text}\n==========================================================\n")
        return True

    url = f"https://graph.facebook.com/v21.0/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code in [200, 201]:
                logger.info(f"WhatsApp message successfully sent to {clean_phone}")
                return True
            else:
                logger.error(f"WhatsApp API Error ({response.status_code}): {response.text}")
                print(f"[WhatsApp API Error] {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error calling WhatsApp API: {e}")
        return False

async def notify_owner_new_booking(alert_text: str):
    """
    Sends an instant WhatsApp alert directly to the clinic owner.
    """
    owner_phone = config.CLINIC_OWNER_PHONE
    if owner_phone:
        logger.info(f"Notifying clinic owner at {owner_phone}")
        await send_whatsapp_message(owner_phone, alert_text)
    else:
        logger.warning("No CLINIC_OWNER_PHONE configured in .env; skipping owner notification.")
        print(f"\n[ALERT TO CLINIC OWNER (SIMULATED)]:\n{alert_text}\n")
