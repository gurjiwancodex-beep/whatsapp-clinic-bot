const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, Browsers, delay } = require('@whiskeysockets/baileys');
const qrcodeTerminal = require('qrcode-terminal');
const QRCode = require('qrcode');
const pino = require('pino');
const path = require('path');
const fs = require('fs');
const readline = require('readline');
const { exec } = require('child_process');

// Primary cloud API endpoint + local fallback
const CLOUD_API_URL = 'https://whatsapp-clinic-bot-1.onrender.com/api/chat';
const LOCAL_API_URL = 'http://127.0.0.1:8000/api/chat';

function askQuestion(query) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    return new Promise(resolve => rl.question(query, ans => {
        rl.close();
        resolve(ans.trim());
    }));
}

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

async function startBridge() {
    const authDir = path.join(__dirname, 'auth_session');
    if (!fs.existsSync(authDir)) {
        fs.mkdirSync(authDir, { recursive: true });
    }

    const { state, saveCreds } = await useMultiFileAuthState(authDir);
    const { version } = await fetchLatestBaileysVersion();

    const isRegistered = Boolean(state.creds && state.creds.registered);

    let usePairingCode = false;
    let phoneNumber = '';

    if (!isRegistered) {
        console.log('\n================================================================');
        console.log('       📱 WHATSAPP CONNECT KARAN DA TARIQA CHUNO');
        console.log('================================================================');
        console.log('  [1] 8-Digit Pairing Code (RECOMMENDED - No Camera / Zero Error)');
        console.log('  [2] QR Code (Camera Scan)');
        console.log('================================================================\n');

        const choice = await askQuestion('Option number pao [1 ya 2, default is 1]: ');

        if (choice === '2') {
            usePairingCode = false;
        } else {
            usePairingCode = true;
            const inputPhone = await askQuestion('Apna WhatsApp Phone Number pao (Country code 91 naal, e.g. 919876543210): ');
            phoneNumber = inputPhone.replace(/[^0-9]/g, '');
            if (!phoneNumber) {
                console.log('❌ Invalid phone number! Defaulting to QR code.');
                usePairingCode = false;
            }
        }
    }

    console.log(`\nConnecting to WhatsApp Web (Baileys v${version.join('.')})...`);

    const sock = makeWASocket({
        version,
        auth: state,
        printQRInTerminal: false,
        logger: pino({ level: 'silent' }),
        browser: Browsers.ubuntu('Chrome'),
        syncFullHistory: false
    });

    sock.ev.on('creds.update', saveCreds);

    if (usePairingCode && !isRegistered && phoneNumber) {
        setTimeout(async () => {
            try {
                const code = await sock.requestPairingCode(phoneNumber);
                console.log('\n****************************************************************');
                console.log('🎉 TUHADA WHATSAPP 8-DIGIT PAIRING CODE:');
                console.log('');
                console.log(`               👉   ${code}   👈`);
                console.log('');
                console.log('****************************************************************');
                console.log('1. Apne iPhone/Phone ch WhatsApp open karo');
                console.log('2. Settings (ya 3 dots) -> "Linked Devices" -> "Link a Device" dabao');
                console.log('3. Screen de thalle "Link with phone number instead" te click karo');
                console.log(`4. Eh 8-digit code [ ${code} ] apne phone vich pao!`);
                console.log('****************************************************************\n');
            } catch (err) {
                console.error('Error getting pairing code:', err.message);
            }
        }, 3000);
    }

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr && !usePairingCode && !isRegistered) {
            console.log('\n======================================================');
            console.log('📱 WHATSAPP QR CODE SCAN KARO:');
            console.log('1. Apne mobile ch WhatsApp open karo');
            console.log('2. Settings -> "Linked Devices" -> "Link a Device"');
            console.log('3. Thalle dita QR Code scan karo:');
            console.log('======================================================\n');
            
            qrcodeTerminal.generate(qr, { small: true });

            try {
                const dataUrl = await QRCode.toDataURL(qr, { width: 340, margin: 2 });
                const qrHtmlPath = path.join(__dirname, 'qr.html');
                const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"><title>Scan WhatsApp QR Code</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0b141a; color: #e9edef; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: #111b21; border: 1px solid #222e35; padding: 32px; border-radius: 20px; text-align: center; max-width: 440px; }
        h2 { color: #00a884; margin-top: 0; }
        .qr-wrapper { background: white; padding: 16px; border-radius: 16px; display: inline-block; margin: 15px 0; }
        ol { text-align: left; line-height: 1.8; color: #d1d7db; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📱 WhatsApp Connect Karo</h2>
        <ol>
            <li>Apne phone ch <b>WhatsApp</b> open karo</li>
            <li><b>Linked Devices</b> -> <b>Link a Device</b> dabao</li>
            <li>Is QR Code nu scan karo</li>
        </ol>
        <div class="qr-wrapper"><img src="${dataUrl}" width="280" height="280" /></div>
        <div style="color:#00a884;font-weight:600;">✓ Zero GST • Real WhatsApp Active</div>
    </div>
</body>
</html>`;
                fs.writeFileSync(qrHtmlPath, htmlContent);
                if (!hasOpenedBrowser) {
                    hasOpenedBrowser = true;
                    exec(`start "" "${qrHtmlPath}"`);
                }
            } catch (err) {}
            console.log('======================================================\n');
        }

        if (connection === 'close') {
            const statusCode = (lastDisconnect?.error)?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
            console.log(`Connection closed (Code: ${statusCode}). Reconnecting: ${shouldReconnect}`);

            if (shouldReconnect) {
                setTimeout(startBridge, 3000);
            } else {
                console.log('⚠️ Logged out. Delete auth_session folder to re-pair.');
            }
        } else if (connection === 'open') {
            console.log('\n🎉 ======================================================');
            console.log('✅ WHATSAPP SUCCESSFULLY CONNECTED!');
            console.log('🤖 Clinic AI Bot is LIVE on Real WhatsApp!');
            console.log('Now any message sent to this number will get AI reply!');
            console.log('======================================================\n');
        }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            if (!msg.message || msg.key.fromMe) continue;

            const remoteJid = msg.key.remoteJid;
            if (!remoteJid || remoteJid.endsWith('@g.us') || remoteJid === 'status@broadcast') continue;

            const senderPhone = remoteJid.replace(/@.+/, '');
            const messageText = msg.message.conversation ||
                                msg.message.extendedTextMessage?.text ||
                                msg.message.imageMessage?.caption ||
                                '';

            if (!messageText.trim()) continue;

            console.log(`\n📩 [Message from +${senderPhone}]: ${messageText}`);

            try {
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
                console.error(`Error forwarding message: ${err.message}`);
            }
        }
    });
}

startBridge().catch(err => {
    console.error('Fatal initialization error:', err);
});
