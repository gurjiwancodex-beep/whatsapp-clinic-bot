import logging
from fastapi import FastAPI, Request, Query, HTTPException, BackgroundTasks, Form
from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
import config
import database
import ai_service
import whatsapp_service
import clinic_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("whatsapp_clinic_bot")

app = FastAPI(title="WhatsApp AI Clinic Bot", version="1.0.0")

@app.get("/")
def home():
    info = clinic_manager.get_current_clinic_info()
    return {
        "status": "online",
        "clinic": info.get("clinic_name"),
        "doctor": info.get("doctor_name"),
        "endpoints": {
            "whatsapp_chat": "/chat (Instant WhatsApp Mobile Simulator)",
            "admin": "/admin (Mobile & Desktop Clinic Info Manager)",
            "appointments": "/appointments (Live Bookings Dashboard)",
            "meta_webhook": "/webhook (Meta WhatsApp)",
            "twilio_webhook": "/twilio-webhook (Twilio WhatsApp)",
            "health": "/health"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# ========================================================
# 1. INSTANT WHATSAPP WEB UI FOR MOBILE (/chat)
# ========================================================
@app.get("/chat", response_class=HTMLResponse)
def whatsapp_mobile_chat():
    info = clinic_manager.get_current_clinic_info()
    clinic_name = info.get("clinic_name", "Clinic")
    doctor_name = info.get("doctor_name", "Doctor")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>{clinic_name} - WhatsApp</title>
        <style>
            * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background: #e5ddd5;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            .header {{
                background: #075e54;
                color: white;
                padding: 10px 14px;
                display: flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            .avatar {{
                width: 42px;
                height: 42px;
                border-radius: 50%;
                background: #128c7e;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
            }}
            .header-info {{ flex: 1; }}
            .header-name {{ font-weight: 600; font-size: 16px; margin: 0; }}
            .header-status {{ font-size: 12px; opacity: 0.85; margin: 0; }}
            .chat-box {{
                flex: 1;
                overflow-y: auto;
                padding: 14px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            .msg {{
                max-width: 80%;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 14.5px;
                line-height: 1.4;
                position: relative;
                word-wrap: break-word;
                box-shadow: 0 1px 1px rgba(0,0,0,0.1);
            }}
            .msg.bot {{
                background: #ffffff;
                align-self: flex-start;
                border-top-left-radius: 0;
            }}
            .msg.user {{
                background: #dcf8c6;
                align-self: flex-end;
                border-top-right-radius: 0;
            }}
            .msg-time {{
                font-size: 10.5px;
                color: #888;
                text-align: right;
                margin-top: 4px;
            }}
            .typing {{
                font-style: italic;
                color: #555;
                font-size: 13px;
                display: none;
                padding: 6px 12px;
                background: rgba(255,255,255,0.7);
                border-radius: 12px;
                align-self: flex-start;
            }}
            .input-bar {{
                background: #f0f0f0;
                padding: 8px 10px;
                display: flex;
                gap: 8px;
                align-items: center;
            }}
            .input-box {{
                flex: 1;
                background: white;
                border: none;
                border-radius: 24px;
                padding: 10px 16px;
                font-size: 15px;
                outline: none;
            }}
            .send-btn {{
                background: #128c7e;
                color: white;
                border: none;
                width: 44px;
                height: 44px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="avatar">🩺</div>
            <div class="header-info">
                <p class="header-name">{clinic_name}</p>
                <p class="header-status" id="status-text">{doctor_name} • 24/7 AI Assistant</p>
            </div>
            <a href="/admin" style="color: white; text-decoration: none; font-size: 12px; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 6px;">⚙️ Admin</a>
        </div>

        <div class="chat-box" id="chat">
            <div class="msg bot">
                Sat Sri Akal ji! 🙏 Welcome to {clinic_name}.<br>
                Mai {doctor_name} ji da AI assistant haan. Assi tuhanu kis trah madad kar sakde haan? 🏥
                <div class="msg-time">Just now</div>
            </div>
            <div class="typing" id="typing">ਬੋਟ ਟਾਈਪ ਕਰ ਰਿਹਾ ਹੈ... (typing...)</div>
        </div>

        <form class="input-bar" id="chat-form">
            <input type="text" id="user-input" class="input-box" placeholder="Type a message (ਪੰਜਾਬੀ / English)..." autocomplete="off" required>
            <button type="submit" class="send-btn">➤</button>
        </form>

        <script>
            const form = document.getElementById('chat-form');
            const input = document.getElementById('user-input');
            const chat = document.getElementById('chat');
            const typing = document.getElementById('typing');
            const senderId = 'web_user_' + Math.floor(Math.random() * 10000);

            function scrollToBottom() {{
                chat.scrollTop = chat.scrollHeight;
            }}

            form.addEventListener('submit', async (e) => {{
                e.preventDefault();
                const text = input.value.trim();
                if (!text) return;

                // Add User Message
                const userMsg = document.createElement('div');
                userMsg.className = 'msg user';
                userMsg.innerHTML = text + '<div class="msg-time">Now ✓✓</div>';
                chat.insertBefore(userMsg, typing);
                input.value = '';
                scrollToBottom();

                // Show typing indicator
                typing.style.display = 'block';
                scrollToBottom();

                try {{
                    const res = await fetch('/api/chat', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ sender_id: senderId, message: text }})
                    }});
                    const data = await res.json();
                    
                    typing.style.display = 'none';
                    const botMsg = document.createElement('div');
                    botMsg.className = 'msg bot';
                    botMsg.innerHTML = data.reply.replace(/\\n/g, '<br>') + '<div class="msg-time">Now</div>';
                    chat.insertBefore(botMsg, typing);
                    scrollToBottom();
                }} catch (err) {{
                    typing.style.display = 'none';
                    const errMsg = document.createElement('div');
                    errMsg.className = 'msg bot';
                    errMsg.innerText = 'Error connecting to bot server.';
                    chat.insertBefore(errMsg, typing);
                    scrollToBottom();
                }}
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/api/chat")
async def api_chat(payload: dict):
    sender_id = payload.get("sender_id", "web_patient")
    message = payload.get("message", "").strip()
    
    if not message:
        return {"reply": "Please enter a message."}
        
    database.save_message(sender_id=sender_id, role="user", message=message)
    reply = await ai_service.generate_bot_reply(sender_id=sender_id, incoming_text=message)
    database.save_message(sender_id=sender_id, role="model", message=reply)
    
    return {"reply": reply}

# ========================================================
# 2. TWILIO WHATSAPP WEBHOOK (/twilio-webhook)
# ========================================================
@app.post("/twilio-webhook")
async def handle_twilio_message(request: Request):
    try:
        form_data = await request.form()
        from_number = form_data.get("From", "")
        body_text = form_data.get("Body", "").strip()
        clean_phone = from_number.replace("whatsapp:", "").strip()
        
        if clean_phone and body_text:
            database.save_message(sender_id=clean_phone, role="user", message=body_text)
            ai_reply = await ai_service.generate_bot_reply(sender_id=clean_phone, incoming_text=body_text)
            database.save_message(sender_id=clean_phone, role="model", message=ai_reply)
            
            safe_reply = ai_reply.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_reply}</Message>
</Response>"""
            return Response(content=twiml, media_type="application/xml")
            
        return Response(content="<Response/>", media_type="application/xml")
    except Exception as e:
        logger.error(f"Error handling Twilio webhook: {e}")
        return Response(content="<Response/>", media_type="application/xml")

# ========================================================
# 3. META WEBHOOK VERIFICATION & HANDLER (/webhook)
# ========================================================
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == config.WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook successfully verified by Meta!")
        return PlainTextResponse(content=hub_challenge, status_code=200)
    else:
        raise HTTPException(status_code=403, detail="Verification token mismatch")

async def process_incoming_message(sender_id: str, incoming_text: str):
    try:
        database.save_message(sender_id=sender_id, role="user", message=incoming_text)
        ai_reply = await ai_service.generate_bot_reply(sender_id=sender_id, incoming_text=incoming_text)
        database.save_message(sender_id=sender_id, role="model", message=ai_reply)
        await whatsapp_service.send_whatsapp_message(to_phone=sender_id, text=ai_reply)
    except Exception as e:
        logger.error(f"Error handling message from {sender_id}: {e}")

@app.post("/webhook")
async def handle_whatsapp_event(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        entries = body.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                for msg in change.get("value", {}).get("messages", []):
                    if msg.get("type") == "text":
                        sender_phone = msg.get("from")
                        text_body = msg.get("text", {}).get("body", "").strip()
                        if sender_phone and text_body:
                            background_tasks.add_task(
                                process_incoming_message,
                                sender_id=sender_phone,
                                incoming_text=text_body
                            )
        return JSONResponse(content={"status": "EVENT_RECEIVED"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": "ERROR", "detail": str(e)}, status_code=200)

# ========================================================
# 4. MOBILE ADMIN PANEL (/admin)
# ========================================================
@app.get("/admin", response_class=HTMLResponse)
def admin_page(saved: bool = False):
    info = clinic_manager.load_local_info()
    saved_banner = """
    <div style="background: #dcfce7; border: 1px solid #86efac; color: #166534; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: 500;">
        ✅ ਸਾਰੀ ਜਾਣਕਾਰੀ ਅਪਡੇਟ ਹੋ ਗਈ ਹੈ! (Information updated successfully in AI memory!)
    </div>
    """ if saved else ""

    checked_attr = "checked" if info.get("is_doctor_on_leave") else ""

    html = f"""
    <!DOCTYPE html>
    <html lang="pa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ਕਲੀਨਿਕ ਮੈਨੇਜਰ - Clinic Admin</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f1f5f9; padding: 16px; margin: 0; }}
            .card {{ max-width: 650px; margin: auto; background: white; padding: 24px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
            h2 {{ margin-top: 0; color: #0f172a; font-size: 22px; }}
            p.sub {{ color: #64748b; font-size: 14px; margin-top: -6px; margin-bottom: 20px; }}
            .form-group {{ margin-bottom: 16px; }}
            label {{ display: block; font-weight: 600; color: #334155; margin-bottom: 6px; font-size: 14px; }}
            input[type="text"], textarea {{ width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 15px; font-family: inherit; }}
            .leave-box {{ background: #fef2f2; border: 1px solid #fecaca; padding: 14px; border-radius: 10px; margin-bottom: 18px; display: flex; align-items: center; gap: 12px; }}
            .leave-box input {{ transform: scale(1.3); cursor: pointer; }}
            .leave-box label {{ margin: 0; color: #991b1b; font-size: 15px; cursor: pointer; }}
            .btn {{ width: 100%; background: #25D366; color: white; padding: 14px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }}
            .nav {{ display: flex; justify-content: space-between; margin-bottom: 15px; }}
            .nav a {{ color: #2563eb; text-decoration: none; font-size: 14px; font-weight: 500; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="nav">
                <a href="/chat">💬 Open WhatsApp Chat</a>
                <a href="/appointments">📋 View Bookings</a>
            </div>
            <h2>🏥 ਕਲੀਨਿਕ ਜਾਣਕਾਰੀ ਅਪਡੇਟ ਕਰੋ</h2>
            <p class="sub">ਇੱਥੇ ਕੀਤੀ ਕੋਈ ਵੀ ਤਬਦੀਲੀ WhatsApp AI ਤੁਰੰਤ ਸਿੱਖ ਲਵੇਗਾ।</p>
            {saved_banner}
            <form action="/admin" method="post">
                <div class="leave-box">
                    <input type="checkbox" id="leave" name="is_doctor_on_leave" value="true" {checked_attr}>
                    <label for="leave">🚨 <b>ਡਾਕਟਰ ਸਾਹਿਬ ਅੱਜ ਛੁੱਟੀ 'ਤੇ ਹਨ (Doctor On Leave Today)</b></label>
                </div>
                <div class="form-group">
                    <label>ਕਲੀਨਿਕ ਦਾ ਨਾਮ (Clinic Name):</label>
                    <input type="text" name="clinic_name" value="{info.get('clinic_name', '')}" required>
                </div>
                <div class="form-group">
                    <label>ਡਾਕਟਰ ਦਾ ਨਾਮ (Doctor Name):</label>
                    <input type="text" name="doctor_name" value="{info.get('doctor_name', '')}" required>
                </div>
                <div class="form-group">
                    <label>ਟਾਈਮਿੰਗ (Clinic Hours):</label>
                    <input type="text" name="clinic_hours" value="{info.get('clinic_hours', '')}" required>
                </div>
                <div class="form-group">
                    <label>ਫੀਸ (Consultation Fee):</label>
                    <input type="text" name="consultation_fee" value="{info.get('consultation_fee', '')}" required>
                </div>
                <div class="form-group">
                    <label>ਅੱਜ ਦਾ ਖਾਸ ਸੁਨੇਹਾ / ਨੋਟਿਸ (Today's Notice):</label>
                    <textarea name="today_notice" rows="2">{info.get('today_notice', '')}</textarea>
                </div>
                <div class="form-group">
                    <label>ਸੇਵਾਵਾਂ (Services offered):</label>
                    <input type="text" name="services" value="{info.get('services', '')}">
                </div>
                <button type="submit" class="btn">💾 ਅਪਡੇਟ ਸੇਵ ਕਰੋ (Save Updates)</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/admin")
async def update_admin_info(
    clinic_name: str = Form(...),
    doctor_name: str = Form(...),
    clinic_hours: str = Form(...),
    consultation_fee: str = Form(...),
    today_notice: str = Form(""),
    services: str = Form(""),
    is_doctor_on_leave: str = Form(None)
):
    updated_data = {
        "clinic_name": clinic_name.strip(),
        "doctor_name": doctor_name.strip(),
        "clinic_hours": clinic_hours.strip(),
        "consultation_fee": consultation_fee.strip(),
        "today_notice": today_notice.strip(),
        "services": services.strip(),
        "is_doctor_on_leave": True if is_doctor_on_leave else False
    }
    clinic_manager.save_local_info(updated_data)
    return RedirectResponse(url="/admin?saved=true", status_code=303)

# ========================================================
# 5. CLINIC APPOINTMENTS DASHBOARD (/appointments)
# ========================================================
@app.get("/appointments", response_class=HTMLResponse)
def list_appointments():
    info = clinic_manager.get_current_clinic_info()
    appointments = database.get_recent_appointments(limit=50)
    rows_html = ""
    for appt in appointments:
        rows_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">#{appt['id']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: bold;">{appt['patient_name']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{appt['patient_phone']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{appt['appointment_date']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{appt['appointment_time']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{appt['reason']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">
                <span style="background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{appt['status']}</span>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; color: #64748b;">{appt['created_at']}</td>
        </tr>
        """
    if not rows_html:
        rows_html = "<tr><td colspan='8' style='text-align: center; padding: 20px; color: #64748b;'>No appointments booked yet.</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{info.get('clinic_name')} - Booked Appointments</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; padding: 20px; }}
            .container {{ max-width: 1000px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            h1 {{ color: #0f172a; margin-top: 0; }}
            p.sub {{ color: #64748b; margin-top: -5px; margin-bottom: 25px; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th {{ background: #f1f5f9; padding: 12px 10px; color: #334155; font-size: 14px; }}
            .nav-link {{ display: inline-block; margin-bottom: 15px; color: #2563eb; text-decoration: none; font-weight: 500; font-size: 14px; margin-right: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div>
                <a href="/chat" class="nav-link">💬 Open Live Chat</a>
                <a href="/admin" class="nav-link">⚙️ Clinic Admin Settings</a>
            </div>
            <h1>🏥 {info.get('clinic_name')}</h1>
            <p class="sub">Doctor: <b>{info.get('doctor_name')}</b> | Live Appointments Dashboard</p>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th><th>Patient Name</th><th>Phone</th><th>Date</th><th>Time</th><th>Reason</th><th>Status</th><th>Booked At</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
