import makeWASocket, { 
    DisconnectReason, 
    useMultiFileAuthState,
    downloadMediaMessage,
    getContentType
} from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import pino from 'pino';
import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import mime from 'mime-types';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.BAILEYS_PORT || 3033;
const AUTH_DIR = path.join(__dirname, '..', 'auth');
const DOWNLOADS_DIR = path.join(__dirname, '..', 'downloads');

if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true });
if (!fs.existsSync(DOWNLOADS_DIR)) fs.mkdirSync(DOWNLOADS_DIR, { recursive: true });

let sock = null;
let qrCode = null;
let connectionStatus = 'disconnected';
let messageHandlers = [];

const logger = pino({ level: 'silent' });

async function connectWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    
    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        logger: logger,
        browser: ['AJ8 WhatsApp', 'Chrome', '120.0.0']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            qrCode = qr;
            connectionStatus = 'qr_pending';
            console.log('QR Code generated - scan with WhatsApp');
        }
        
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error instanceof Boom)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('Connection closed, reconnecting:', shouldReconnect);
            connectionStatus = 'disconnected';
            if (shouldReconnect) {
                setTimeout(connectWhatsApp, 5000);
            }
        } else if (connection === 'open') {
            console.log('WhatsApp connected!');
            connectionStatus = 'connected';
            qrCode = null;
        }
    });

    sock.ev.on('messages.upsert', async (m) => {
        if (m.type !== 'notify') return;
        
        for (const msg of m.messages) {
            if (msg.key.fromMe) continue;
            
            const messageData = await processMessage(msg);
            
            for (const handler of messageHandlers) {
                try {
                    await handler(messageData);
                } catch (err) {
                    console.error('Handler error:', err);
                }
            }
        }
    });

    return sock;
}

async function processMessage(msg) {
    const messageType = getContentType(msg.message);
    const chatId = msg.key.remoteJid;
    const sender = msg.key.participant || chatId;
    const isGroup = chatId.endsWith('@g.us');
    
    let content = {
        id: msg.key.id,
        chatId,
        sender,
        isGroup,
        timestamp: msg.messageTimestamp,
        type: messageType,
        text: null,
        media: null
    };

    if (messageType === 'conversation') {
        content.text = msg.message.conversation;
    } else if (messageType === 'extendedTextMessage') {
        content.text = msg.message.extendedTextMessage.text;
    }

    if (['imageMessage', 'videoMessage', 'audioMessage', 'documentMessage', 'stickerMessage'].includes(messageType)) {
        try {
            const buffer = await downloadMediaMessage(msg, 'buffer', {}, {
                logger,
                reuploadRequest: sock.updateMediaMessage
            });
            
            const mediaInfo = msg.message[messageType];
            const extension = getExtensionForType(messageType, mediaInfo.mimetype);
            const filename = `${msg.key.id}.${extension}`;
            const filepath = path.join(DOWNLOADS_DIR, filename);
            
            fs.writeFileSync(filepath, buffer);
            
            content.media = {
                type: messageType.replace('Message', ''),
                mimetype: mediaInfo.mimetype,
                filename: filepath,
                size: buffer.length,
                duration: mediaInfo.seconds || null,
                isVoiceNote: messageType === 'audioMessage' && mediaInfo.ptt === true
            };
            
            if (content.media.isVoiceNote) {
                content.media.waveform = mediaInfo.waveform || null;
            }
            
        } catch (err) {
            console.error('Error downloading media:', err);
        }
    }

    return content;
}

function getExtensionForType(type, mimetype) {
    if (mimetype) {
        const ext = mime.extension(mimetype);
        if (ext) return ext;
    }
    
    switch (type) {
        case 'imageMessage': return 'jpg';
        case 'videoMessage': return 'mp4';
        case 'audioMessage': return 'ogg';
        case 'stickerMessage': return 'webp';
        case 'documentMessage': return 'bin';
        default: return 'bin';
    }
}

app.get('/status', (req, res) => {
    res.json({
        status: connectionStatus,
        qrCode: qrCode,
        user: sock?.user || null
    });
});

app.get('/qr', (req, res) => {
    if (qrCode) {
        res.json({ qr: qrCode });
    } else if (connectionStatus === 'connected') {
        res.json({ message: 'Already connected', status: 'connected' });
    } else {
        res.json({ message: 'No QR code available', status: connectionStatus });
    }
});

app.post('/send', async (req, res) => {
    const { phone, message, mediaPath, mediaType } = req.body;
    
    if (!sock || connectionStatus !== 'connected') {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }
    
    try {
        const jid = phone.includes('@') ? phone : `${phone}@s.whatsapp.net`;
        
        if (mediaPath && fs.existsSync(mediaPath)) {
            const buffer = fs.readFileSync(mediaPath);
            const mimetype = mime.lookup(mediaPath) || 'application/octet-stream';
            
            let content;
            if (mediaType === 'audio' || mimetype.startsWith('audio/')) {
                content = { audio: buffer, mimetype, ptt: true };
            } else if (mediaType === 'image' || mimetype.startsWith('image/')) {
                content = { image: buffer, caption: message || '' };
            } else if (mediaType === 'video' || mimetype.startsWith('video/')) {
                content = { video: buffer, caption: message || '' };
            } else {
                content = { document: buffer, mimetype, fileName: path.basename(mediaPath) };
            }
            
            const result = await sock.sendMessage(jid, content);
            res.json({ success: true, messageId: result.key.id });
        } else {
            const result = await sock.sendMessage(jid, { text: message });
            res.json({ success: true, messageId: result.key.id });
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/chats', async (req, res) => {
    if (!sock || connectionStatus !== 'connected') {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }
    
    try {
        const chats = await sock.groupFetchAllParticipating();
        const chatList = Object.values(chats).map(chat => ({
            id: chat.id,
            name: chat.subject,
            isGroup: true,
            participants: chat.participants?.length || 0
        }));
        res.json(chatList);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/webhook/register', (req, res) => {
    const { url } = req.body;
    
    if (!url) {
        return res.status(400).json({ error: 'URL required' });
    }
    
    const handler = async (message) => {
        try {
            await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(message)
            });
        } catch (err) {
            console.error('Webhook error:', err);
        }
    };
    
    messageHandlers.push(handler);
    res.json({ success: true, message: 'Webhook registered' });
});

app.get('/downloads/:filename', (req, res) => {
    const filepath = path.join(DOWNLOADS_DIR, req.params.filename);
    if (fs.existsSync(filepath)) {
        res.sendFile(filepath);
    } else {
        res.status(404).json({ error: 'File not found' });
    }
});

app.listen(PORT, () => {
    console.log(`Baileys API running on port ${PORT}`);
    connectWhatsApp();
});
