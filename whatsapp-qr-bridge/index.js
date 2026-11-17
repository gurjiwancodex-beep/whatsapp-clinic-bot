const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, Browsers } = require('@whiskeysockets/baileys');
const qrcodeTerminal = require('qrcode-terminal');
const QRCode = require('qrcode');
const pino = require('pino');
const path = require('path');
const fs = require('fs');
const readline = require('readline');
const { exec } = require('child_process');

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

function cleanPhoneNumber(input) {
    let clean = input.replace(/[^0-9]/g, '');
    if (clean.startsWith('0')) {
        clean = clean.substring(1);
    }
    // Auto-prepend 91 if user entered 10 digits
    if (clean.length === 10) {
        clean = '91' + clean;
    }
    return clean;
}

async function getAvailableApiUrl() {
    try {
        const res = await fetch(LOCAL_API_URL.replace('/api/chat', '/docs'), { signal: AbortSignal.timeout(1500) });
        if (res.ok) {
            return LOCAL_API_URL;
        }
    } catch (e) {}
    return CLOUD_API_URL;
}

let hasOpenedCodeBrowser = false;

async function startBridge() {
    const authDir = path.join(__dirname, 'auth_session');
    if (!fs.existsSync(authDir)) {
        fs.mkdirSync(authDir, { recursive: true });
    }

    const { state, saveCreds } = await useMultiFileAuthState(authDir);
    const { version } = await fetchLatestBaileysVersion();

    const isRegistered = Boolean(state.creds && state.creds.registered);

    let usePairingCode = true;
    let phoneNumber = '917814924900';

    if (!isRegistered) {
        console.log('\n================================================================');
        console.log('       📱 WHATSAPP CONNECT KARAN DA TARIQA');
        console.log('================================================================');
        console.log('  [1] 8-Digit Pairing Code (Phone Number - Instant Link)');
        console.log('  [2] QR Code (Camera Scan)');
        console.log('================================================================\n');

        const choice = await askQuestion('Option chuno [1 ya 2, default 1]: ');

        if (choice === '2') {
            usePairingCode = false;
        } else {
            usePairingCode = true;
            const inputPhone = await askQuestion('Apna WhatsApp Number pao [Press Enter for 7814924900]: ');
            if (inputPhone) {
                phoneNumber = cleanPhoneNumber(inputPhone);
            } else {
                phoneNumber = '917814924900';
            }
            console.log(`\nPhone number formatted: +${phoneNumber}`);
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
                const rawCode = await sock.requestPairingCode(phoneNumber);
                const formattedCode = rawCode.match(/.{1,4}/g)?.join('-') || rawCode;

                console.log('\n****************************************************************');
                console.log('🎉 TUHADA WHATSAPP 8-DIGIT PAIRING CODE TAYAR HAI:');
                console.log('');
                console.log(`               👉   ${formattedCode}   👈`);
                console.log('');
                console.log('****************************************************************');
                console.log('📱 IPHONE / PHONE VICH KIDAN BHARNA HAI:');
                console.log('1. Apne phone ch WhatsApp open karo');
                console.log('2. Settings -> "Linked Devices" -> "Link a Device" te click karo');
                console.log('3. Screen de thalle "Link with phone number instead" te click karo');
                console.log(`4. Eh code bharo:   ${formattedCode}`);
                console.log('****************************************************************\n');

                try {
                    const codeHtmlPath = path.join(__dirname, 'pairing_code.html');
                    const html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WhatsApp Pairing Code</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, sans-serif; background: #0b141a; color: #e9edef; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .card { background: #111b21; border: 1px solid #222e35; padding: 35px; border-radius: 20px; text-align: center; max-width: 460px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h2 { color: #00a884; margin-top: 0; font-size: 24px; }
        .code-box { background: #202c33; border: 2px dashed #00a884; border-radius: 14px; padding: 18px 25px; margin: 25px 0; font-size: 38px; font-weight: bold; letter-spacing: 5px; color: #25d366; user-select: all; }
        ol { text-align: left; line-height: 1.8; color: #d1d7db; font-size: 15px; padding-left: 20px; }
        .note { font-size: 13px; color: #8696a0; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📱 WhatsApp Pairing Code</h2>
        <p style="color:#8696a0;">Target Number: <b>+${phoneNumber}</b></p>
        <div class="code-box">${formattedCode}</div>
        <ol>
            <li>Apne phone ch <b>WhatsApp</b> open karo</li>
            <li><b>Settings</b> -> <b>Linked Devices</b> -> <b>Link a Device</b> dabao</li>
            <li>Screen de thalle <b>"Link with phone number instead"</b> te tap karo</li>
            <li>Eh 8-digit code pao: <b>${formattedCode}</b></li>
        </ol>
        <div class="note">✓ Code paande hi 1 second ch connect ho javega!</div>
    </div>
</body>
</html>`;
                    fs.writeFileSync(codeHtmlPath, html);
                    if (!hasOpenedCodeBrowser) {
                        hasOpenedCodeBrowser = true;
                        exec(`start "" "${codeHtmlPath}"`);
                    }
                } catch (e) {}
            } catch (err) {
                console.error('Error getting pairing code:', err.message);
            }
        }, 3000);
    }

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr && !usePairingCode && !isRegistered) {
            console.log('\n======================================================');
            console.log('📱 WHATSAPP QR CODE:');
            console.log('======================================================\n');
            qrcodeTerminal.generate(qr, { small: true });
        }

        if (connection === 'close') {
            const statusCode = (lastDisconnect?.error)?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
            console.log(`Connection closed (Code: ${statusCode}). Reconnecting: ${shouldReconnect}`);

            if (shouldReconnect) {
                setTimeout(startBridge, 3000);
            } else {
                console.log('⚠️ Device logged out. Delete auth_session folder to re-pair.');
            }
        } else if (connection === 'open') {
            console.log('\n🎉 ======================================================');
            console.log('✅ WHATSAPP SUCCESSFULLY CONNECTED!');
            console.log(`🤖 Clinic AI Bot is LIVE on Real WhatsApp (+${phoneNumber})!`);
            console.log('Huun kisi vi number ton WhatsApp te message bhej k test karo!');
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
