#!/usr/bin/env python3
import re
from datetime import datetime
from collections import OrderedDict

TIMELINE = "/home/ubuntu/.openclaw/workspace/journal/TIMELINE.md"
OUTPUT = "/var/www/html/journal/index.html"

def parse_entries(content):
    entries = []
    blocks = re.split(r'\n---\n', content)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith('#'):
            continue    
        entries.append(block)
    return entries

def render_entry(entry):
    ts_match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)\]', entry)
    you_match = re.search(r'You: (.+?)(?=Ghost:|$)', entry, re.DOTALL)
    ghost_match = re.search(r'Ghost: (.+?)(?=Tags:|$)', entry, re.DOTALL)
    tags_match = re.search(r'Tags: (.+?)$', entry, re.MULTILINE)
    pipe_match = re.match(r'\[(.+?)\] \| (.+?) \| (.+?) \| (.+)', entry)
    
    gps_html = ""
    weather_html = ""
    you_html = ""


    if ts_match and ghost_match:
        ts = ts_match.group(1)
        you = you_match.group(1).strip() if you_match else ""
        ghost = ghost_match.group(1).strip()
        tags = tags_match.group(1).strip() if tags_match else ""
        tag_html = " ".join(f'<span class="tag">{t.strip()}</span>' for t in tags.split() if t.startswith("#")) if tags else ""
        you_html = f'<div class="you"><span class="label">You</span> {you}</div>' if you else ""
        gps_match = re.search(r'GPS: (.+?)$', entry, re.MULTILINE)
        gps = gps_match.group(1).strip() if gps_match else ""
        gps_html = f'<div class="gps"><span class="label">GPS</span> {gps}</div>' if gps else ""
        weather_match = re.search(r'Weather: (.+?)$', entry, re.MULTILINE)
        weather = weather_match.group(1).strip() if weather_match else ""
        weather_html = f'<div class="weather"><span class="label">Weather</span> {weather}</div>' if weather else ""
        return f'''        <div class="entry">
            <div class="timestamp">{ts}</div>
            {you_html}
            {gps_html}
            {weather_html}            
            <div class="ghost"><span class="label">Ghost</span> {ghost}</div>
             {f'<div class="tags">{tag_html}</div>' if tag_html else ""}
        </div>'''
    elif pipe_match:
        ts = pipe_match.group(1)
        location = pipe_match.group(2)
        fact = pipe_match.group(3)
        reflection = pipe_match.group(4)
        return f'''        <div class="entry">
            <div class="timestamp">{ts}</div>
            <div class="location">{location}</div>
            <div class="ghost"><span class="label">Ghost</span> {fact}</div>
            <div class="reflection"><em>{reflection}</em></div>
        </div>'''
    return ""
def main():
    try:
        with open(TIMELINE) as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    entries = [e for e in parse_entries(content) if e]
    
    # Group by date
    grouped = OrderedDict()
    for entry in entries:
        ts_match = re.match(r'\[(\d{4}-\d{2}-\d{2})', entry)
        date = ts_match.group(1) if ts_match else "Unknown"
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(entry)
    
    # Render grouped
    grouped = OrderedDict(sorted(grouped.items(), reverse=True))    
    sections = []
    for date, day_entries in grouped.items():
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            date_label = dt.strftime("%A %-d %B %Y").upper()
        except:
            date_label = date
        def get_time(e):
            m = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)\]', e)
            return m.group(1) if m else ""
        day_entries.sort(key=get_time)
        entries_html = "\n".join(render_entry(e) for e in day_entries if e)
        sections.append(f'<div class="day-header">{date_label}</div>\n{entries_html}')
    
    entry_html = "\n".join(sections)
    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ghost of the City - Chronicle</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#128065;</text></svg>">
    <style>
        body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; max-width: 680px; margin: 0 auto; padding: 3rem 2rem; background: #ffffff; color: #111; line-height: 1.6; }
        h1 { font-size: 0.75rem; letter-spacing: 0.2em; text-transform: uppercase; color: #111; border-bottom: 2px solid #111; padding-bottom: 0.75rem; margin-bottom: 3rem; font-weight: 400; }
        .entry { margin-bottom: 3rem; padding-bottom: 3rem; border-bottom: 1px solid #e0e0e0; }
        .timestamp { font-size: 0.65rem; color: #999; letter-spacing: 0.15em; margin-bottom: 1rem; text-transform: uppercase; }
        .location { font-size: 0.8rem; color: #555; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.1em; }
        .label { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.15em; color: #999; margin-right: 0.75rem; font-weight: 600; }
        .you { color: #555; font-style: italic; margin-bottom: 1rem; font-size: 0.9rem; }
        .ghost { color: #111; margin-bottom: 1rem; font-size: 1rem; }
        .reflection { color: #555; font-size: 0.9rem; border-left: 2px solid #111; padding-left: 1rem; margin-top: 0.5rem; }
        .gps { font-size: 0.65rem; color: #999; font-family: monospace; margin-bottom: 0.75rem; }    
        .weather { font-size: 0.65rem; color: #999; font-family: monospace; margin-bottom: 0.75rem; }        
        .tag { font-size: 0.65rem; background: #f0f0f0; color: #555; padding: 0.2rem 0.5rem; margin-right: 0.3rem; font-family: monospace; }
        .updated { font-size: 0.65rem; color: #bbb; text-align: right; margin-top: 3rem; letter-spacing: 0.1em; text-transform: uppercase; }
        .day-header { font-size: 0.7rem; letter-spacing: 0.2em; text-transform: uppercase; color: #111; border-top: 2px solid #111; padding-top: 0.75rem; margin: 3rem 0 2rem 0; font-weight: 600; }
    </style>
</head>
<body>
    <h1>Ghost of the City &mdash; Chronicle</h1>
    ENTRY_PLACEHOLDER
    <div class="updated">Last updated: UPDATED_PLACEHOLDER</div>
</body>
</html>"""

    html = html.replace("ENTRY_PLACEHOLDER", entry_html)
    html = html.replace("UPDATED_PLACEHOLDER", updated)

    with open(OUTPUT, "w") as f:
        f.write(html)
    print("Journal rendered.")

if __name__ == "__main__":
    main()
