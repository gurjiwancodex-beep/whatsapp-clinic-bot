import json
import logging
import time
from pathlib import Path
from typing import Dict, Any
import httpx

logger = logging.getLogger(__name__)

INFO_FILE = Path(__file__).resolve().parent / "clinic_info.json"

DEFAULT_INFO = {
    "clinic_name": "Sharma Health Clinic",
    "doctor_name": "Dr. Sharma",
    "clinic_hours": "Monday to Saturday: 10:00 AM - 2:00 PM, 5:00 PM - 8:00 PM. Sunday: Closed.",
    "consultation_fee": "₹300",
    "is_doctor_on_leave": False,
    "today_notice": "ਡਾਕਟਰ ਸਾਹਿਬ ਅੱਜ ਆਮ ਵਾਂਗ ਉਪਲਬਧ ਹਨ। (Doctor is available today as usual.)",
    "services": "General Checkup, Fever, Cough, Diabetes, Blood Pressure, Child Health",
    "google_sheet_csv_url": ""
}

# In-memory cache for Google Sheet data
_sheet_cache = {"timestamp": 0, "data": {}}
CACHE_TTL_SECONDS = 120  # 2 minutes

def load_local_info() -> Dict[str, Any]:
    if not INFO_FILE.exists():
        save_local_info(DEFAULT_INFO)
        return DEFAULT_INFO.copy()
    try:
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for k, v in DEFAULT_INFO.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        logger.error(f"Error reading clinic_info.json: {e}")
        return DEFAULT_INFO.copy()

def save_local_info(data: Dict[str, Any]):
    try:
        with open(INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving clinic_info.json: {e}")

def fetch_google_sheet_info(csv_url: str) -> Dict[str, Any]:
    """
    Fetches published Google Sheet CSV and parses Key, Value pairs.
    """
    now = time.time()
    if now - _sheet_cache["timestamp"] < CACHE_TTL_SECONDS and _sheet_cache["data"]:
        return _sheet_cache["data"]

    try:
        response = httpx.get(csv_url, timeout=5.0)
        if response.status_code == 200:
            lines = response.text.splitlines()
            sheet_dict = {}
            for line in lines:
                parts = [p.strip().strip('"') for p in line.split(",", 1)]
                if len(parts) == 2:
                    k, v = parts[0].lower().replace(" ", "_"), parts[1]
                    sheet_dict[k] = v
            
            _sheet_cache["timestamp"] = now
            _sheet_cache["data"] = sheet_dict
            return sheet_dict
    except Exception as e:
        logger.warning(f"Could not fetch Google Sheet CSV: {e}")

    return {}

def get_current_clinic_info() -> Dict[str, Any]:
    """
    Returns latest clinic info, merging local config with Google Sheet if configured.
    """
    info = load_local_info()
    sheet_url = info.get("google_sheet_csv_url", "").strip()

    if sheet_url:
        sheet_data = fetch_google_sheet_info(sheet_url)
        if sheet_data:
            if "clinic_name" in sheet_data:
                info["clinic_name"] = sheet_data["clinic_name"]
            if "doctor_name" in sheet_data:
                info["doctor_name"] = sheet_data["doctor_name"]
            if "clinic_hours" in sheet_data:
                info["clinic_hours"] = sheet_data["clinic_hours"]
            if "consultation_fee" in sheet_data:
                info["consultation_fee"] = sheet_data["consultation_fee"]
            if "today_notice" in sheet_data:
                info["today_notice"] = sheet_data["today_notice"]
            if "is_doctor_on_leave" in sheet_data:
                info["is_doctor_on_leave"] = sheet_data["is_doctor_on_leave"].lower() in ["yes", "true", "1"]

    return info
