const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const qrcodeTerminal = require('qrcode-terminal');
const QRCode = require('qrcode');
const pino = require('pino');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');

// Primary cloud API endpoint + local fallback
const CLOUD_API_URL = 'https://whatsapp-clinic-bot-1.onrender.com/api/chat';
const LOCAL_API_URL = 'http://127.0.0.1:8000/api/chat';

async function getAvailableApiUrl() {
    try {
        const res = await fetch(LOCAL_API_URL.replace('/api/chat', '/docs'), { signal: AbortSignal.timeout(1500) });
        if (res.ok) {
            return LOCAL_API_URL;
        }
    } catch (e) {
        // Local server not running, use cloud server
    }
    return CLOUD_API_URL;
}

let hasOpenedBrowser = false;

async function connectToWhatsApp() {
    const authDir = path.join(__dirname, 'auth_session');
    if (!fs.existsSync(authDir)) {
        fs.mkdirSync(authDir, { recursive: true });
    }

    const { state, saveCreds } = await useMultiFileAuthState(authDir);
    const { version } = await fetchLatestBaileysVersion();

    console.log(`Connecting to WhatsApp Web using Baileys v${version.join('.')}`);

    const sock = makeWASocket({
        version,
        auth: state,
        printQRInTerminal: false,
        logger: pino({ level: 'error' }),
        browser: ['Clinic WhatsApp Bot', 'Chrome', '120.0.0.0']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n======================================================');
            console.log('📱 WHATSAPP QR CODE SCAN KARO:');
            console.log('1. Apne mobile ch WhatsApp open karo');
            console.log('2. Three dots (⋮) ya Settings -> "Linked Devices" te click karo');
            console.log('3. "Link a Device" daba k thalle dita QR Code scan karo:');
            console.log('======================================================\n');
            
            qrcodeTerminal.generate(qr, { small: true });

            // Also generate HTML visual file and open in browser for effortless scanning
            try {
                const dataUrl = await QRCode.toDataURL(qr, { width: 340, margin: 2 });
                const qrHtmlPath = path.join(__dirname, 'qr.html');
                const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Scan WhatsApp QR Code</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background: #0b141a; color: #e9edef; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: #111b21; border: 1px solid #222e35; padding: 32px; border-radius: 20px; text-align: center; max-width: 440px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h2 { color: #00a884; margin-top: 0; font-size: 24px; }
        p { color: #8696a0; font-size: 14px; margin-bottom: 20px; }
        ol { text-align: left; font-size: 14px; color: #d1d7db; line-height: 1.8; padding-left: 20px; margin-bottom: 24px; }
        .qr-wrapper { background: white; padding: 16px; border-radius: 16px; display: inline-block; box-shadow: 0 4px 16px rgba(0,0,0,0.3); }
        img { display: block; }
        .badge { display: inline-block; background: rgba(0,168,132,0.15); color: #00a884; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📱 WhatsApp Connect Karo</h2>
        <p>Singla Eye Care AI Bot nu link karan layi instructions:</p>
        <ol>
            <li>Apne phone ch <b>WhatsApp</b> open karo</li>
            <li>Menu (3 dots ⋮ ya Settings) te tap karo</li>
            <li><b>Linked Devices</b> select karo</li>
            <li><b>Link a Device</b> daba k thalle dita QR Code scan karo</li>
        </ol>
        <div class="qr-wrapper">
            <img src="${dataUrl}" alt="WhatsApp QR Code" width="280" height="280" />
        </div>
        <div>
            <span class="badge">✓ Zero Setup Fees • No GST Required • 24/7 AI</span>
        </div>
    </div>
</body>
</html>`;
                fs.writeFileSync(qrHtmlPath, htmlContent);
                console.log(`🌐 Browser ch QR Code open ho reha hai: ${qrHtmlPath}`);
                if (!hasOpenedBrowser) {
                    hasOpenedBrowser = true;
                    exec(`start "" "${qrHtmlPath}"`);
                }
            } catch (err) {
                // Non-critical, terminal QR is already available
            }

            console.log('======================================================\n');
        }

        if (connection === 'close') {
            const statusCode = (lastDisconnect?.error)?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
            console.log(`Connection closed (Code: ${statusCode}). Reconnecting: ${shouldReconnect}`);

            if (shouldReconnect) {
                setTimeout(connectToWhatsApp, 3000);
            } else {
                console.log('⚠️ Device logged out. Delete auth_session folder to scan a new QR code.');
            }
        } else if (connection === 'open') {
            console.log('\n🎉 ======================================================');
            console.log('✅ WHATSAPP SUCCESSFULLY CONNECTED!');
            console.log('Bot is LIVE! Incoming messages will get instant AI replies.');
            console.log('======================================================\n');

            try {
                const qrHtmlPath = path.join(__dirname, 'qr.html');
                const connectedHtml = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"><title>WhatsApp Connected</title>
    <style>body{font-family:system-ui;background:#0b141a;color:#e9edef;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;}.card{background:#111b21;padding:40px;border-radius:20px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,0.5);border:1px solid #222e35;}h1{color:#00a884;}p{color:#8696a0;}</style>
</head>
<body><div class="card"><h1>🎉 WhatsApp Connected!</h1><p>Bot live chal reha hai. Kisi vi number ton WhatsApp te message bhej k test karo!</p></div></body>
</html>`;
                fs.writeFileSync(qrHtmlPath, connectedHtml);
            } catch (e) {}
        }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            // Ignore messages sent by bot or system
            if (!msg.message || msg.key.fromMe) continue;

            const remoteJid = msg.key.remoteJid;
            // Ignore group chats and status updates
            if (!remoteJid || remoteJid.endsWith('@g.us') || remoteJid === 'status@broadcast') continue;

            const senderPhone = remoteJid.replace(/@.+/, '');
            const messageText = msg.message.conversation ||
                                msg.message.extendedTextMessage?.text ||
                                msg.message.imageMessage?.caption ||
                                '';

            if (!messageText.trim()) continue;

            console.log(`\n📩 [Message from +${senderPhone}]: ${messageText}`);

            try {
                // Indicate typing
                await sock.sendPresenceUpdate('composing', remoteJid);

                const apiUrl = await getAvailableApiUrl();
                const res = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        sender_id: senderPhone,
                        message: messageText
                    })
                });

                if (!res.ok) {
                    console.error(`Backend returned HTTP ${res.status}`);
                    continue;
                }

                const data = await res.json();
                const replyText = data.reply;

                if (replyText) {
                    await sock.sendPresenceUpdate('paused', remoteJid);
                    await sock.sendMessage(remoteJid, { text: replyText });
                    console.log(`🤖 [Replied to +${senderPhone}]:\n${replyText}\n`);
                }
            } catch (err) {
                console.error(`Error processing message: ${err.message}`);
            }
        }
    });
}

connectToWhatsApp().catch(err => {
    console.error('Fatal initialization error:', err);
});
