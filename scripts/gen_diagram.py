#!/usr/bin/env python3
"""Generate the Ghost of the City architecture diagram as light/dark SVGs."""
import os

FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'SF Mono', Menlo, Consolas, monospace"

def box(x, y, w, h, title, sub=None, dashed=False):
    cx = x + w / 2
    dash = ' stroke-dasharray="5 4"' if dashed else ''
    s = f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="INK" stroke-width="1"{dash}/>\n'
    if sub:
        s += (f'  <text x="{cx}" y="{y+h/2-3}" text-anchor="middle" font-family="{FONT}" font-size="12.5" '
              f'letter-spacing="1.3" fill="INK">{title}</text>\n')
        s += (f'  <text x="{cx}" y="{y+h/2+16}" text-anchor="middle" font-family="{MONO}" font-size="9.5" '
              f'fill="MID">{sub}</text>\n')
    else:
        s += (f'  <text x="{cx}" y="{y+h/2+4}" text-anchor="middle" font-family="{FONT}" font-size="12.5" '
              f'letter-spacing="1.3" fill="INK">{title}</text>\n')
    return s

def label(x, y, text, anchor="middle", size=9.5, fill="MID", mono=True, spacing=0.4):
    f = MONO if mono else FONT
    return (f'  <text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{f}" font-size="{size}" '
            f'letter-spacing="{spacing}" fill="{fill}">{text}</text>\n')

def line(pts, dashed=False, arrow="end", width=1):
    d = ' stroke-dasharray="5 4"' if dashed else ''
    m = ''
    if arrow in ("end", "both"):
        m += ' marker-end="url(#ah)"'
    if arrow in ("start", "both"):
        m += ' marker-start="url(#ahs)"'
    p = " ".join(f"{a},{b}" for a, b in pts)
    return f'  <polyline points="{p}" fill="none" stroke="INK" stroke-width="{width}"{d}{m}/>\n'

W, H = 960, 520
s = []
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">\n')
s.append('  <title id="t">Ghost of the City — system architecture</title>\n')
s.append('  <desc id="d">A live voice loop (device to Apache to OpenClaw gateway to Claude) and a '
         'separate five-minute cron pipeline that turns session logs into the rendered journal page. '
         'The two meet at the gateway and again at Apache.</desc>\n')
s.append('  <defs>\n'
         '    <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">\n'
         '      <path d="M 0 1 L 9 5 L 0 9 z" fill="INK"/>\n'
         '    </marker>\n'
         '    <marker id="ahs" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">\n'
         '      <path d="M 0 1 L 9 5 L 0 9 z" fill="INK"/>\n'
         '    </marker>\n'
         '  </defs>\n')

# --- context files feeding the model ---
s.append(box(710, 25, 100, 45, "SOUL.md", "persona"))
s.append(box(820, 25, 100, 45, "GHOST_DATA", "15 sites"))
s.append(line([(760, 70), (760, 116)]))
s.append(line([(870, 70), (870, 116)]))

# --- Row A: the live loop ---
s.append(box(40, 120, 150, 70, "RABBIT R1", "voice in / out"))
s.append(box(250, 120, 160, 70, "APACHE", ":443 + /journal"))
s.append(box(470, 120, 180, 70, "OPENCLAW GATEWAY", ":18789"))
s.append(box(710, 120, 210, 70, "CLAUDE SONNET 4.6", "API · Bedrock fallback"))

s.append(line([(190, 155), (248, 155)], arrow="both"))
s.append(label(219, 146, "WSS"))
s.append(line([(410, 155), (468, 155)], arrow="both"))
s.append(label(439, 146, "proxy"))
s.append(line([(650, 155), (708, 155)], arrow="both"))
s.append(label(679, 146, "HTTPS"))

# --- divider ---
s.append(f'  <line x1="40" y1="258" x2="920" y2="258" stroke="RULE" stroke-width="1"/>\n')
s.append(label(920, 249, "ASYNCHRONOUS · EVERY 5 MINUTES", anchor="end", size=9, spacing=1.6))

# --- Row B: the batch pipeline (flows right to left) ---
s.append(box(745, 310, 175, 70, "SESSION LOGS", ".jsonl", dashed=True))
s.append(box(505, 310, 200, 70, "chronicle_update.py", "cron · GPS + weather", dashed=True))
s.append(box(315, 310, 150, 70, "TIMELINE.md", "the Chronicle", dashed=True))
s.append(box(75, 310, 200, 70, "journal_render.py", "cron · renders HTML", dashed=True))

s.append(line([(743, 345), (707, 345)], dashed=True))
s.append(line([(503, 345), (467, 345)], dashed=True))
s.append(line([(313, 345), (277, 345)], dashed=True))

# gateway writes the session logs
s.append(line([(560, 190), (560, 278), (832, 278), (832, 308)], dashed=True))
s.append(label(638, 271, "writes .jsonl"))

# renderer writes the page Apache serves
s.append(line([(175, 308), (175, 232), (330, 232), (330, 192)], dashed=True))
s.append(label(253, 224, "writes index.html"))

# --- external enrichment ---
s.append(box(470, 430, 140, 48, "NOMINATIM", "name → lat/lon", dashed=True))
s.append(box(640, 430, 130, 48, "WTTR.IN", "London weather", dashed=True))
s.append(line([(540, 428), (540, 382)], dashed=True))
s.append(line([(700, 428), (700, 382)], dashed=True))

s.append('</svg>\n')
svg = "".join(s)

THEMES = {
    "light": {"INK": "#111111", "MID": "#777777", "RULE": "#dddddd"},
    "dark":  {"INK": "#e6e6e6", "MID": "#9aa0a6", "RULE": "#30363d"},
}
out = os.path.expanduser("~/Documents/projects/ghost-city/publish/images")
for name, c in THEMES.items():
    t = svg
    for k, v in c.items():
        t = t.replace(k, v)
    p = os.path.join(out, f"architecture-{name}.svg")
    open(p, "w").write(t)
    print(f"wrote {p}  ({len(t):,} bytes)")
