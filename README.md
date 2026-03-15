# Pearl's Kick Extension

A powerful Microsoft Edge/Opera extension for Kick.com that automates chat interactions and tracks your channel points in real time.

---

## Features

### 🤖 Auto Chat
Automatically sends a custom message to chat at a configurable interval. Useful for repeating commands, social links, or any recurring message. Minimum interval is 5 seconds.

### 🔁 Echo Response
Reacts to chat messages in real time. When a viewer types a configured trigger word or emote, the extension automatically replies with a set answer.

- Supports multiple triggers and answers (comma-separated)
- Index-based matching — each trigger maps to its own answer
- Wildcard `*` — echoes the trigger back as the reply
- Configurable delay before responding
- Configurable cooldown between responses
- **Hype Mode** — only responds when the same trigger appears 2× within 8 seconds

### ⏰ Scheduled Messages
Schedule messages to be sent automatically at a specific time on selected days of the week. Supports multiple scheduled entries, each with its own message, time, and day selector. Scheduled state persists across browser restarts.

### 💰 Custom Points System (Made for MarweX's stream and his web mwx.cz)
Fetches your channel points from an external API and displays them directly in the Kick navbar. Updates automatically every 60 seconds and after every sent message.

- Points widget embedded in the Kick navbar with a pulse animation on update
- Only visible on your configured allowed channel
- Configurable API URL

---

## Installation

1. Download the latest `.zip` from [Releases](../../releases)
2. Unzip the file
3. Open Chrome or Opera and go to `chrome://extensions`
4. Enable **Developer mode**
5. Click **Load unpacked** and select the unzipped folder

---

## Usage

1. Click the extension icon to open the popup
2. Enable the **master toggle** at the top
3. Configure and enable individual features as needed
4. Click **💾 Save & Restart** to apply changes

---

## Screenshots

> Coming soon

---

## Privacy

Pearl's Kick Extension stores all settings locally in your browser using `chrome.storage.local`. No data is sent to any external server except the API URL you configure yourself for point tracking. The extension only interacts with Kick.com and your configured API endpoint.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## Discord

Have questions, suggestions, or just want to hang out?

Join the **Pearl Studios** Discord: [discord.gg/qZNkGHYBK8](https://discord.gg/qZNkGHYBK8)

---

## License

MIT
