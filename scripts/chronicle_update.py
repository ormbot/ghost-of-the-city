#!/usr/bin/env python3
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone

SESSIONS_DIR = os.path.expanduser("~/.openclaw/agents/main/sessions")
TIMELINE = os.path.expanduser("~/.openclaw/workspace/journal/TIMELINE.md")

def get_existing_timestamps():
    if not os.path.exists(TIMELINE):
        return set()
    with open(TIMELINE) as f:
        content = f.read()
    return set(re.findall(r'(?:# SKIP )?\[?(\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)\]?', content))

def clean_user_text(text):
    text = re.sub(r'Sender \(untrusted metadata\):\s*```json.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\[.*?UTC\]\s*', '', text)
    return text.strip()

def clean_ghost_text(text):
    text = re.sub(r'\[\[.*?\]\]\s*', '', text)
    return text.strip()

def get_coordinates(text):
    try:
        text = text.rstrip('.,!?')

        filler = r"^(so |now |and |also |I'?m |I am |standing |stood |looking at |in front of |at |near |on |in |the |a |an |by |outside |beside |next to |around |behind )"
        prev = None
        while text != prev:
            prev = text
            text = re.sub(filler, "", text.strip(), flags=re.IGNORECASE)

        text = re.sub(r"\s+(?:in|near|at|by|around)\s+[\w\s']+$", '', text, flags=re.IGNORECASE).strip()

        def try_nominatim(q):
            encoded = urllib.parse.quote(q + ", London")
            url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": "GhostCityChronicle/1.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())

        query = text.strip()[:80]
        data = try_nominatim(query)

        # Retry: drop last word (e.g. "Smithfield Meat Market" -> "Smithfield Market")
        if not data:
            words = query.split()
            if len(words) > 1:
                data = try_nominatim(" ".join(words[:-1]))

        # Retry: drop last two words (e.g. "Smithfield Meat Market" -> "Smithfield")
        if not data:
            words = query.split()
            if len(words) > 2:
                data = try_nominatim(" ".join(words[:-2]))

        # Retry: strip apostrophes (speech-to-text artefacts like "Drop's" -> "Drops")
        if not data:
            data = try_nominatim(query.replace("'", ""))

        if data:
            lat = round(float(data[0]["lat"]), 4)
            lon = round(float(data[0]["lon"]), 4)
            return f"{lat}, {lon}"
    except:
        pass
    return None

def get_weather():
    try:
        url = "https://wttr.in/London?format=%t+%C"
        req = urllib.request.Request(url, headers={"User-Agent": "GhostCityChronicle/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read().decode("utf-8").strip()
    except:
        return None

def parse_session(filepath):
    entries = []
    messages = []
    with open(filepath) as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                if obj.get("type") == "message":
                    messages.append(obj)
            except:
                continue

    for i, msg in enumerate(messages):
        role = msg.get("message", {}).get("role")
        if role != "assistant":
            continue

        content = msg.get("message", {}).get("content", [])
        assistant_text = ""
        for block in content:
            if block.get("type") == "text":
                assistant_text = block.get("text", "")
                break

        if not assistant_text:
            continue

        user_text = ""
        for j in range(i-1, -1, -1):
            prev = messages[j].get("message", {})
            if prev.get("role") == "user":
                content_blocks = prev.get("content", [])
                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if isinstance(block, dict) and block.get("type") == "text":
                            user_text = block.get("text", "")
                            break
                elif isinstance(content_blocks, str):
                    user_text = content_blocks
                break

        if not user_text:
            continue

        user_text = clean_user_text(user_text)
        assistant_text = clean_ghost_text(assistant_text)

        if not user_text or not assistant_text:
            continue

        ts = msg.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            formatted_ts = dt.strftime("%Y-%m-%d %H:%M UTC")
        except:
            continue

        entries.append({
            "timestamp": formatted_ts,
            "user": user_text,
            "ghost": assistant_text
        })

    return entries

def main():
    existing = get_existing_timestamps()
    new_entries = []

    for fname in sorted(os.listdir(SESSIONS_DIR)):
        if not fname.endswith(".jsonl"):
            continue
        fpath = os.path.join(SESSIONS_DIR, fname)
        entries = parse_session(fpath)
        for entry in entries:
            if entry["timestamp"] not in existing:
                new_entries.append(entry)

    if not new_entries:
        print("No new entries to add.")
        return

    with open(TIMELINE, "a") as f:
        for entry in new_entries:
            coords = get_coordinates(entry["user"])
            weather = get_weather()
            f.write(f"\n[{entry['timestamp']}]\n")
            if coords:
                f.write(f"GPS: {coords}\n")
            if weather:
                f.write(f"Weather: {weather}\n")
            f.write(f"You: {entry['user']}\n")
            f.write(f"Ghost: {entry['ghost']}\n")
            f.write("---\n")

    print(f"Added {len(new_entries)} new entries to Chronicle.")

if __name__ == "__main__":
    main()
