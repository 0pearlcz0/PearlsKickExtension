#!/usr/bin/env python3
"""
Pearl's Kick Extension - Stats Backend API
FastAPI server with SQLite database
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import secrets
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
import os

app = FastAPI(title="Pearl Stats API", version="1.0.0")

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "stats.db"

# ── DATABASE ──────────────────────────────────────────────────────────
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                token TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                type TEXT NOT NULL,
                text TEXT,
                FOREIGN KEY (token) REFERENCES tokens(token)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mute_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                chat_before TEXT NOT NULL,
                my_before TEXT NOT NULL,
                FOREIGN KEY (token) REFERENCES tokens(token)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_token ON messages(token)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mutes_token ON mute_incidents(token)")
        conn.commit()

# ── MODELS ────────────────────────────────────────────────────────────
class Message(BaseModel):
    timestamp: str
    type: str  # auto_chat, echo, manual, scheduled
    text: Optional[str] = None

class MuteIncident(BaseModel):
    timestamp: str
    chat_before: List[dict]  # [{timestamp, username, text}, ...]
    my_before: List[dict]    # [{timestamp, type, text}, ...]

class SubmitBatch(BaseModel):
    token: str
    messages: List[Message] = []
    mute_incidents: List[MuteIncident] = []

class StatsResponse(BaseModel):
    total_messages: int
    messages_24h: int
    messages_7d: int
    messages_30d: int
    by_type: dict
    mute_count: int
    recent_mutes: List[dict]
    hourly_chart: List[dict]  # [{hour, count}, ...]

# ── ENDPOINTS ─────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the dashboard HTML"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        # Replace localhost with actual server URL
        html_content = html_content.replace(
            "const API_URL = 'http://localhost:8000';",
            "const API_URL = window.location.origin;"
        )
        return html_content
    return {"status": "ok", "api": "Pearl Stats API v1.0.0"}

@app.post("/api/submit")
def submit_batch(batch: SubmitBatch):
    """Submit a batch of messages and mute incidents"""
    with get_db() as conn:
        # Ensure token exists
        conn.execute("INSERT OR IGNORE INTO tokens (token) VALUES (?)", (batch.token,))
        
        # Insert messages
        for msg in batch.messages:
            conn.execute(
                "INSERT INTO messages (token, timestamp, type, text) VALUES (?, ?, ?, ?)",
                (batch.token, msg.timestamp, msg.type, msg.text)
            )
        
        # Insert mute incidents
        for mute in batch.mute_incidents:
            conn.execute(
                "INSERT INTO mute_incidents (token, timestamp, chat_before, my_before) VALUES (?, ?, ?, ?)",
                (batch.token, mute.timestamp, json.dumps(mute.chat_before), json.dumps(mute.my_before))
            )
        
        conn.commit()
    
    return {"status": "ok", "messages": len(batch.messages), "mutes": len(batch.mute_incidents)}

@app.get("/api/stats/{token}", response_model=StatsResponse)
def get_stats(token: str):
    """Get statistics for a token"""
    with get_db() as conn:
        # Check if token exists
        row = conn.execute("SELECT * FROM tokens WHERE token = ?", (token,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Token not found")
        
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Total messages
        total = conn.execute("SELECT COUNT(*) FROM messages WHERE token = ?", (token,)).fetchone()[0]
        
        # Messages in time windows
        msg_24h = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE token = ? AND timestamp >= ?",
            (token, day_ago.isoformat())
        ).fetchone()[0]
        
        msg_7d = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE token = ? AND timestamp >= ?",
            (token, week_ago.isoformat())
        ).fetchone()[0]
        
        msg_30d = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE token = ? AND timestamp >= ?",
            (token, month_ago.isoformat())
        ).fetchone()[0]
        
        # By type
        by_type = {}
        rows = conn.execute(
            "SELECT type, COUNT(*) as count FROM messages WHERE token = ? GROUP BY type",
            (token,)
        ).fetchall()
        for row in rows:
            by_type[row['type']] = row['count']
        
        # Mutes
        mute_count = conn.execute("SELECT COUNT(*) FROM mute_incidents WHERE token = ?", (token,)).fetchone()[0]
        
        # Recent mutes (last 10)
        recent_mutes = []
        rows = conn.execute(
            "SELECT * FROM mute_incidents WHERE token = ? ORDER BY timestamp DESC LIMIT 10",
            (token,)
        ).fetchall()
        for row in rows:
            recent_mutes.append({
                "timestamp": row['timestamp'],
                "chat_before": json.loads(row['chat_before']),
                "my_before": json.loads(row['my_before'])
            })
        
        # Hourly chart (last 24h)
        hourly_chart = []
        for i in range(24):
            hour_start = now - timedelta(hours=23-i)
            hour_end = hour_start + timedelta(hours=1)
            count = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE token = ? AND timestamp >= ? AND timestamp < ?",
                (token, hour_start.isoformat(), hour_end.isoformat())
            ).fetchone()[0]
            hourly_chart.append({
                "hour": hour_start.strftime("%H:%M"),
                "count": count
            })
        
        return StatsResponse(
            total_messages=total,
            messages_24h=msg_24h,
            messages_7d=msg_7d,
            messages_30d=msg_30d,
            by_type=by_type,
            mute_count=mute_count,
            recent_mutes=recent_mutes,
            hourly_chart=hourly_chart
        )

# ── STARTUP ───────────────────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    init_db()
    print("✅ Database initialized")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=25574)
