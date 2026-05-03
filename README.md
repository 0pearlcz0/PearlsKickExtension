# Pearl's Kick Extension v2.1.0 - Statistics System

## Co je hotové

### ✅ Backend API (`/home/claude/pearls-stats-backend/`)
- **main.py** - FastAPI server s SQLite databází
- **requirements.txt** - Python dependencies
- **index.html** - Web dashboard pro zobrazení statistik

### ✅ Extension soubory (částečně)
- **manifest.json** - Aktualizováno na v2.1.0
- **popup.html** - Odstraněn Custom Body, přidána Stats sekce
- **popup.css** - Přidány styly pro stats
- **popup.js** - Odstraněny customBody odkazy, přidán token management
- **background.js** - Odstraněn points fetching, pouze scheduled messages
- **content.js** - ⚠️ **POTŘEBUJE DOKONČENÍ** (viz níže)

## Co zbývá dokončit v content.js

1. **Odstranit navbar widget** (řádky 390-580)
   - `findNavbarTarget()`
   - `createWidget()`
   - `removeWidget()`
   - `injectStyle()` pro widget
   - `setWidgetPoints()`
   - Storage listener pro points

2. **Přidat stats tracking**:
   ```javascript
   // Buffer pro zprávy a mute incidenty
   let messageBuffer = [];
   let muteBuffer = [];
   let lastChatMessages = []; // posledních 10 ze všech
   let myRecentMessages = []; // posledních 10 mých
   
   // Trackování odeslané zprávy
   function trackMessage(type, text) {
     messageBuffer.push({
       timestamp: new Date().toISOString(),
       type, // auto_chat, echo, manual, scheduled
       text
     });
     myRecentMessages.push({...});
     if (myRecentMessages.length > 10) myRecentMessages.shift();
   }
   
   // Detekce mute
   function handleMuteDetection() {
     muteBuffer.push({
       timestamp: new Date().toISOString(),
       chat_before: [...lastChatMessages],
       my_before: [...myRecentMessages]
     });
     
     // Pausnout auto chat a echo
     chrome.storage.local.get('pearlState', ({pearlState: s}) => {
       s.autoChat.enabled = false;
       s.echo.enabled = false;
       chrome.storage.local.set({pearlState: s});
       chrome.runtime.sendMessage({type: 'BROADCAST_RELOAD'});
     });
   }
   
   // Upravit sendMessage() aby volal trackMessage()
   // a detekoval selhání (timeout 2s bez zprávy v chatu = mute)
   
   // Observer pro všechny chat zprávy
   // - ukládat do lastChatMessages
   
   // Každých 60s posílat batch na backend
   async function sendStatsToBackend() {
     const token = await chrome.storage.local.get('statsToken');
     fetch('http://localhost:8000/api/submit', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({
         token: token.statsToken,
         messages: messageBuffer,
         mute_incidents: muteBuffer
       })
     });
     messageBuffer = [];
     muteBuffer = [];
   }
   setInterval(sendStatsToBackend, 60000);
   ```

## Instalace

### Backend
```bash
cd /home/claude/pearls-stats-backend
pip install -r requirements.txt
python main.py
# Server běží na http://localhost:8000
```

### Extension
1. Dokončit content.js (viz výše)
2. Zabalit do ZIP
3. Nainstalovat do Chrome/Opera

### Web Dashboard
- Otevřít `http://localhost:8000/index.html`
- Zadat token z extension popupu

## Jak to funguje

1. Extension generuje unikátní 20-char token při prvním spuštění
2. Každá odeslaná zpráva se trackuje (typ + text + timestamp)
3. Při detekci mute se uloží:
   - 10 posledních chat zpráv (všech uživatelů)
   - 10 posledních mých zpráv
   - Auto chat + echo se automaticky pausne
4. Každou minutu se batch pošle na backend API
5. Backend ukládá do SQLite databáze
6. Web dashboard zobrazuje:
   - Celkový počet zpráv (24h/7d/30d)
   - Graf zpráv po hodinách
   - Breakdown podle typu (auto_chat/echo/manual/scheduled)
   - Seznam mute incidentů s kontextem

## Úpravy pro produkci

V `index.html` změň:
```javascript
const API_URL = 'http://localhost:8000';
```
Na:
```javascript
const API_URL = 'https://your-server.com';
```

V `popup.js` změň:
```javascript
viewStatsLink.href = `http://localhost:8000/?token=${token}`;
```
Na:
```javascript
viewStatsLink.href = `https://your-server.com/?token=${token}`;
```

## Další kroky

Řekni mi:
1. Mám dokončit content.js tracking? (odstranit widget + přidat stats)
2. Mám vytvořit finální ZIP ready k nahrání?
3. Chceš nějaké změny v backend API nebo web dasboard?
