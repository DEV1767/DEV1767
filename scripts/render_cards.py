#!/usr/bin/env python3
"""Render every README card into cards/*.svg.

Reads data/contributions.json (refreshed daily by the GitHub Action).
Run with STATIC=1 to draw the final frame with no animation (for screenshots).
"""
import base64, datetime as dt, json, os, pathlib
from xml.sax.saxutils import escape as esc

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
OUT.mkdir(exist_ok=True)
STATIC = os.environ.get("STATIC") == "1"

# ---------- palette (paper + ink + bold colour) ----------
PAPER, INK, MUTED, LINE = "#FFF8EA", "#15171F", "#5E6275", "#15171F"
BLUE, RED, YELLOW, GREEN, PINK = "#2F5BFF", "#FF4D3D", "#FFC933", "#3DDC97", "#FF8AC4"
TINT = {BLUE: "#DCE5FF", RED: "#FFDAD5", YELLOW: "#FFF0BD", GREEN: "#D2F5E5", PINK: "#FFE0F0"}
LEVELS = ["#EEE6D2", "#FFE08A", "#FFAE42", "#FF6B4A", "#D6243B"]   # sunset heat
CYAN = BLUE  # legacy name

# ---------- fonts (embedded so they work inside <img>) ----------
FONT_FILES = {
    "orb800": ("Orbitron", 800, "orbitron-800.woff"),
    "orb700": ("Orbitron", 700, "orbitron-700.woff"),
    "fira": ("Fira Code", 400, "firacode-400.woff"),
}
_b64 = {k: base64.b64encode((ROOT / "fonts" / v[2]).read_bytes()).decode() for k, v in FONT_FILES.items()}


def font_css(*keys):
    return "".join(
        f"@font-face{{font-family:'{FONT_FILES[k][0]}';font-weight:{FONT_FILES[k][1]};"
        f"src:url(data:font/woff;base64,{_b64[k]}) format('woff')}}"
        for k in keys
    )


BASE_CSS = """
.o{font-family:'Orbitron',sans-serif}.f{font-family:'Fira Code',monospace}
@keyframes fade{from{opacity:0}}
@keyframes rise{from{opacity:0;transform:translateY(14px)}}
@keyframes pop{from{opacity:0;transform:scale(.2)}60%{transform:scale(1.25)}}
@keyframes grow{from{transform:scaleY(0)}}
@keyframes swing{from{opacity:0;transform:translateY(34px) rotate(-3deg)}
  60%{opacity:1;transform:translateY(-5px) rotate(.8deg)}80%{transform:translateY(1px) rotate(-.2deg)}}
@keyframes beam{from{transform:translateX(-160px)}to{transform:translateX(960px)}}
@keyframes pulse{0%{r:3.5;opacity:1}70%,100%{r:9;opacity:0}}
@keyframes rot{0%{opacity:0;transform:translateY(7px)}3%,22%{opacity:1;transform:none}26%,100%{opacity:0}}
@keyframes blink{50%{opacity:0}}
@keyframes draw{from{transform:scaleX(0)}}
.a{animation-fill-mode:both;animation-timing-function:cubic-bezier(.2,.8,.2,1)}
"""
# What every animated card falls back to when motion is off (or in STATIC mode)
CALM = ".a,.a *{animation:none!important}.l2,.l3,.l4,.cf,.pulse{display:none}"
CSS_END = CALM if STATIC else f"@media (prefers-reduced-motion:reduce){{{CALM}}}"


def svg(w, h, body, fonts, extra_css="", defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
        f"<defs>{defs}<style>{font_css(*fonts)}{BASE_CSS}{extra_css}{CSS_END}</style></defs>{body}</svg>"
    )


def save(name, content):
    (OUT / f"{name}.svg").write_text(content, encoding="utf-8")
    print(f"  cards/{name}.svg  {len(content)/1024:.0f} KB")


def anim(name, dur, delay, extra=""):
    return f'style="animation:{name} {dur}s {delay}s both cubic-bezier(.2,.8,.2,1){extra}"'


def panel(w, h, r=14, fill=None):
    fill = fill or PAPER
    return (
        f'<rect x="6" y="6" width="{w-8}" height="{h-8}" rx="{r}" fill="{INK}"/>'
        f'<rect x="2" y="2" width="{w-8}" height="{h-8}" rx="{r}" fill="{fill}" stroke="{INK}" stroke-width="2"/>'
    )


def countup(x, y, value, cls, size, fill, t0, anchor="start", frames=14, step=0.045):
    """Number that counts up from 0. SMIL frames show one number at a time; CSS reveals the final."""
    out = ""
    if not STATIC:
        for i in range(frames):
            v = round(value * (i / frames) ** 0.6)
            out += (
                f'<text class="cf {cls}" x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
                f'text-anchor="{anchor}" opacity="0">{v}'
                f'<set attributeName="opacity" to="1" begin="{t0 + i*step:.3f}s" dur="{step}s"/></text>'
            )
    end = t0 + frames * step
    out += (
        f'<text class="a {cls}" x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
        f'{anim("fade", .01, f"{end:.3f}")}>{value}</text>'
    )
    return out


# ---------- data ----------
data = json.loads((ROOT / "data" / "contributions.json").read_text())
DAYS = [(dt.date.fromisoformat(d["date"]), d["count"], d["level"]) for d in data["days"]]
TOTAL = sum(c for _, c, _ in DAYS)
ACTIVE = sum(1 for _, c, _ in DAYS if c)
BUSIEST = max(DAYS, key=lambda d: d[1])

longest = run = 0
for _, c, _ in DAYS:
    run = run + 1 if c else 0
    longest = max(longest, run)
current = 0
seq = DAYS[:]
if seq and seq[-1][1] == 0:  # today may not have commits yet; don't break the streak
    seq = seq[:-1]
for _, c, _ in reversed(seq):
    if c:
        current += 1
    else:
        break

# last 12 calendar months ending with the latest day's month
last = DAYS[-1][0]
months = []
y, m = last.year, last.month
for _ in range(12):
    months.append((y, m))
    m -= 1
    if m == 0:
        y, m = y - 1, 12
months.reverse()
month_totals = [sum(c for d, c, _ in DAYS if (d.year, d.month) == ym) for ym in months]

# ---------- extra motion for the colourful theme ----------
POP_CSS = """
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes bar{from{transform:scaleX(0)}}
"""


def clip(cid, w, h, r=14):
    return f'<clipPath id="{cid}"><rect x="2" y="2" width="{w-8}" height="{h-8}" rx="{r}"/></clipPath>'


def pill(x, y, text, fill, tcol, t0, size=13, h=28):
    w = len(text) * size * 0.6 + 28
    return (
        f'<g class="a" style="transform-box:fill-box;transform-origin:center;animation:pop .6s {t0}s both cubic-bezier(.2,.9,.3,1.3)">'
        f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="{h/2}" fill="{fill}" stroke="{INK}" stroke-width="2"/>'
        f'<text class="f" x="{x+w/2:.0f}" y="{y+h/2+size*0.35:.1f}" font-size="{size}" fill="{tcol}" text-anchor="middle">{esc(text)}</text></g>',
        w,
    )


# ---------- 1. hero ----------
TAGLINES = [
    "AI & ML Engineering student at JNNCE, Shivamogga",
    "Building scalable backends with Node.js & MongoDB",
    "Designing secure auth systems with JWT",
    "Exploring RAG, LLMs & Agentic AI",
]


def hero():
    W, H = 800, 280
    rot = ""
    for i, t in enumerate(TAGLINES):
        cx = 62 + len(t) * 9.6 + 4
        rot += (
            f'<g class="l{i+1} a" style="animation:rot 16s {i*4}s infinite both">'
            f'<text class="f" x="40" y="214" font-size="16" fill="{BLUE}">›</text>'
            f'<text class="f" x="62" y="214" font-size="16" fill="{INK}">{esc(t)}</text>'
            f'<rect x="{cx:.0f}" y="201" width="8" height="15" fill="{RED}" style="animation:blink 1s steps(1) infinite"/></g>'
        )
    p1, w1 = pill(40, 128, "Generative AI", BLUE, "#fff", 0.9)
    p2, w2 = pill(40 + w1 + 10, 128, "Agents", RED, "#fff", 1.05)
    p3, _ = pill(40 + w1 + w2 + 20, 128, "Backend", YELLOW, INK, 1.2)
    bars = "".join(
        f'<rect class="a" x="{40+i*78}" y="108" width="70" height="7" rx="3.5" fill="{c}" stroke="{INK}" stroke-width="1.5" '
        f'style="transform-box:fill-box;transform-origin:left;animation:bar .6s {.5+i*.12:.2f}s both cubic-bezier(.2,.8,.2,1)"/>'
        for i, c in enumerate((BLUE, RED, YELLOW))
    )
    shapes = (
        f'<g class="a" style="animation:bob 4s 0s infinite ease-in-out"><circle cx="705" cy="78" r="30" fill="{BLUE}" stroke="{INK}" stroke-width="2.5"/></g>'
        f'<g class="a" style="animation:bob 5s .8s infinite ease-in-out"><rect x="618" y="150" width="52" height="52" rx="8" fill="{RED}" stroke="{INK}" stroke-width="2.5" transform="rotate(14 644 176)"/></g>'
        f'<g class="a" style="animation:bob 4.5s 1.6s infinite ease-in-out"><path d="M726 232 l34 -58 l34 58z" transform="translate(-50 0)" fill="{YELLOW}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/></g>'
    )
    body = (
        panel(W, H)
        + f'<g clip-path="url(#cl)">{shapes}</g>'
        + f'<text class="o a" x="40" y="88" font-size="46" font-weight="800" fill="{INK}" {anim("rise", .9, .15)}>Shivam Chaudhary</text>'
        + bars + p1 + p2 + p3 + rot
        + f'<circle cx="46" cy="256" r="4.5" fill="{GREEN}" stroke="{INK}" stroke-width="1.5"/>'
        + f'<circle class="pulse" cx="46" cy="256" r="4.5" fill="none" stroke="{GREEN}" stroke-width="2" style="animation:pulse 2s 1.5s infinite both"/>'
        + f'<text class="f a" x="62" y="260" font-size="12.5" fill="{MUTED}" {anim("fade", .8, 1.4)}>Open to backend, full-stack and AI collaborations</text>'
    )
    save("hero", svg(W, H, body, ["orb800", "orb700", "fira"], extra_css=POP_CSS, defs=clip("cl", W, H)))


# ---------- 2. contribution graph ----------
def graph():
    W, PAD, GAP = 800, 26, 3.2
    first = DAYS[0][0]
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    cols = (DAYS[-1][0] - start).days // 7 + 1
    pitch = (W - PAD * 2 - 8 + GAP) / cols
    cell = pitch - GAP
    H = 64 + 7 * pitch + 40
    rects, labels, seen = "", "", set()
    for d, c, lv in DAYS:
        col, row = (d - start).days // 7, (d.weekday() + 1) % 7
        x, yy = PAD + col * pitch, 56 + row * pitch
        stroke = f' stroke="{INK}" stroke-width=".8"' if lv else ""
        rects += (
            f'<rect class="a" x="{x:.1f}" y="{yy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.4" fill="{LEVELS[lv]}"{stroke} '
            f'style="animation:pop .45s {0.5 + col*0.028:.2f}s both"/>'
        )
        if (d.day <= 7 and row == 0 and (d.year, d.month) not in seen) or (d.day == 1 and (d.year, d.month) not in seen):
            seen.add((d.year, d.month))
            labels += f'<text class="f" x="{x:.1f}" y="48" font-size="10.5" fill="{MUTED}">{d.strftime("%b")}</text>'
    lx = W - PAD - 8 - 5 * (cell + 4) - 70
    legend = f'<text class="f" x="{lx:.0f}" y="{H-18:.0f}" font-size="10.5" fill="{MUTED}">Less</text>'
    for i, col in enumerate(LEVELS):
        legend += f'<rect x="{lx+32+i*(cell+4):.0f}" y="{H-27:.0f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.4" fill="{col}" stroke="{INK}" stroke-width=".8"/>'
    legend += f'<text class="f" x="{lx+36+5*(cell+4):.0f}" y="{H-18:.0f}" font-size="10.5" fill="{MUTED}">More</text>'
    body = (
        panel(W, round(H))
        + f'<text class="o" x="{PAD}" y="30" font-size="13" font-weight="700" fill="{INK}">Contribution graph</text>'
        + f'<rect x="{PAD+158}" y="19" width="96" height="16" rx="8" fill="{YELLOW}" stroke="{INK}" stroke-width="1.5"/>'
        + f'<text class="f" x="{PAD+206}" y="30.5" font-size="9.5" fill="{INK}" text-anchor="middle">{TOTAL} in 12 mo</text>'
        + labels + rects + legend
    )
    save("graph", svg(W, round(H), body, ["orb700", "fira"]))


# ---------- 3. activity ----------
def activity():
    W, H = 800, 340
    stats = [
        (TOTAL, "contributions", "last 12 months", BLUE, "#fff"),
        (ACTIVE, "active days", "of the last 12 months", RED, "#fff"),
        (longest, "day streak", "longest run", YELLOW, INK),
        (BUSIEST[1], "in one day", BUSIEST[0].strftime("%d %b %Y"), GREEN, INK),
    ]
    body = panel(W, H)
    bw_ = (W - 8 - 48 - 3 * 12) / 4
    for i, (v, l1, l2, fill, tc) in enumerate(stats):
        x = 24 + i * (bw_ + 12)
        body += (
            f'<g class="a" {anim("rise", .6, .3+i*.12)}>'
            f'<rect x="{x:.0f}" y="24" width="{bw_:.0f}" height="92" rx="12" fill="{fill}" stroke="{INK}" stroke-width="2"/>'
            f'<text class="f" x="{x+16:.0f}" y="82" font-size="12" fill="{tc}">{esc(l1)}</text>'
            f'<text class="f" x="{x+16:.0f}" y="100" font-size="10.5" fill="{tc}" opacity=".8">{esc(l2)}</text></g>'
            + countup(round(x + 16), 66, v, "o", 32, tc, 0.7 + i * 0.12)
        )
    body += f'<text class="o" x="26" y="160" font-size="13" font-weight="700" fill="{INK}">Contributions per month</text>'
    base, top = 302, 190
    mx = max(month_totals) or 1
    bw = (W - 8 - 48) / 12
    best = month_totals.index(max(month_totals))
    cyc = [BLUE, RED, YELLOW, GREEN, PINK]
    for i, ((yy, mm), t) in enumerate(zip(months, month_totals)):
        x = 26 + i * bw + 7
        h = max(4, (base - top) * t / mx)
        fill = cyc[i % len(cyc)]
        body += (
            f'<rect class="a" x="{x:.1f}" y="{base-h:.1f}" width="{bw-14:.1f}" height="{h:.1f}" rx="5" fill="{fill}" stroke="{INK}" stroke-width="2" '
            f'style="transform-box:fill-box;transform-origin:bottom;animation:grow .8s {1.2+i*.07:.2f}s both cubic-bezier(.2,.8,.2,1)"/>'
        )
        body += f'<text class="f" x="{x+(bw-14)/2:.1f}" y="{base+18}" font-size="11" fill="{MUTED}" text-anchor="middle">{dt.date(yy, mm, 1).strftime("%b")}</text>'
        if i == best:
            body += (
                f'<text class="o a" x="{x+(bw-14)/2:.1f}" y="{base-h-9:.1f}" font-size="14" font-weight="700" fill="{INK}" '
                f'text-anchor="middle" {anim("pop", .5, 2.2, ";transform-box:fill-box;transform-origin:center")}>{t}</text>'
            )
    save("activity", svg(W, H, body, ["orb700", "fira"]))


# ---------- 4. tiles ----------
TILES = [
    ("Freelance", 1, "live production site", ["Web developer at Indalnova", "Maintains their production site"], BLUE, "#fff"),
    ("Hackathons", 7, "events entered", ["VeriVox AI, Hack Fest 1.0", "Smart India Hackathon (Internal)", "IGNITRON 2K25"], RED, "#fff"),
    ("Learning", 4, "topics in progress", ["LangGraph multi-agent flows", "Advanced RAG", "Vector DB optimization", "System design"], YELLOW, INK),
]


def tiles():
    W, H = 262, 238
    for i, (title, n, label, lines, fill, tc) in enumerate(TILES):
        t0 = 1.9 + i * 0.2
        shine = (
            ""
            if STATIC
            else f'<g clip-path="url(#tc)"><g class="a" style="animation:beam 6s 3s infinite linear both"><rect width="60" height="{H}" fill="#fff" opacity=".22" transform="skewX(-14)"/></g></g>'
        )
        lines_svg = "".join(
            f'<text class="f a" x="34" y="{156+j*18}" font-size="11" fill="{tc}" {anim("fade", .5, t0+.9+j*.12)}>{esc(l)}</text>'
            f'<circle cx="26" cy="{152+j*18}" r="2.5" fill="{tc}"/>'
            for j, l in enumerate(lines)
        )
        body = (
            f'<g class="a" style="transform-box:fill-box;transform-origin:0 100%;animation:swing 1s {t0-.2:.2f}s both cubic-bezier(.2,.9,.3,1.2)">'
            + panel(W, H, fill=fill) + shine
            + f'<text class="o" x="22" y="38" font-size="14" font-weight="700" fill="{tc}">{title}</text>'
            + countup(22, 98, n, "o", 52, tc, t0 + 0.3, frames=8, step=0.08)
            + f'<text class="f" x="22" y="122" font-size="11.5" fill="{tc}">{esc(label)}</text>'
            + f'<line x1="22" y1="134" x2="{W-30}" y2="134" stroke="{tc}" stroke-width="1.5" opacity=".5"/>'
            + lines_svg + "</g>"
        )
        save(f"tile-{title.lower()}", svg(W, H, body, ["orb700", "fira"], defs=clip("tc", W, H)))


# ---------- 5. stack ----------
STACK = [
    ("Backend", BLUE, ["Node.js", "Express", "FastAPI", "JWT"]),
    ("Databases", GREEN, ["MongoDB", "Mongoose", "Redis", "Qdrant"]),
    ("AI / ML", PINK, [ "LangChain", "LangGraph", "Gemini", "Groq"]),
    ("Languages", YELLOW, ["JavaScript", "Python", "C"]),
    ("Tools", RED, ["Git", "GitHub", "VS Code", "Postman"]),
]


def stack():
    W, ROW = 800, 44
    H = 62 + len(STACK) * ROW + 10
    body = panel(W, H) + f'<text class="o" x="26" y="38" font-size="13" font-weight="700" fill="{INK}">Tech stack</text>'
    n = 0
    for r, (cat, col, items) in enumerate(STACK):
        y = 60 + r * ROW
        body += f'<circle cx="32" cy="{y+19}" r="6" fill="{col}" stroke="{INK}" stroke-width="2"/>'
        body += f'<text class="o" x="48" y="{y+23}" font-size="11" font-weight="700" fill="{INK}">{esc(cat)}</text>'
        x = 170
        for it in items:
            w = len(it) * 7.8 + 24
            body += (
                f'<g class="a" {anim("rise", .5, 0.3+n*.05)}>'
                f'<rect x="{x}" y="{y+3}" width="{w:.0f}" height="30" rx="8" fill="{TINT[col]}" stroke="{INK}" stroke-width="2"/>'
                f'<text class="f" x="{x+w/2:.0f}" y="{y+23}" font-size="13" fill="{INK}" text-anchor="middle">{esc(it)}</text></g>'
            )
            x += w + 10
            n += 1
    save("stack", svg(W, H, body, ["orb700", "fira"]))


# ---------- 6. projects ----------
PROJECTS = [
    ("ai-git-rag", "AI & Agentic", "Git RAG", "Agentic GitHub repository assistant",
     ["Repository ingestion and code chunking", "Hybrid retrieval with reranking", "MCP-based tool execution"],
     ["Python", "LangGraph", "LangChain", "MCP", "Qdrant", "FastAPI", "Groq"], BLUE, "#fff"),
    ("ai-commander", "AI & Agentic", "AI Commander", "VS Code AI agent for debugging",
     ["Captures terminal errors from your workflow", "Agent gives context-aware debugging help", "Extension backed by Node.js and FastAPI"],
     ["TypeScript", "VS Code API", "Node.js", "Express", "FastAPI", "LangGraph", "MongoDB", "LLM APIs"], RED, "#fff"),
    ("eventhub", "Backend", "EventHub", "College event management platform",
     ["Built for 1,000+ concurrent users", "Role-based access with JWT auth", "Joi-validated REST APIs, Redis caching"],
     ["Node.js", "Express", "MongoDB", "Mongoose", "Redis", "JWT", "Joi"], YELLOW, INK),
    ("url-shortener", "Backend", "URL Shortener", "Backend service with user accounts",
     ["JWT-based authentication and authorization", "MongoDB persistence", "Redirects to the original URL"],
     ["Node.js", "Express", "MongoDB", "JWT"], GREEN, INK),
]


def projects():
    W, H = 404, 264
    for i, (slug, tag, title, sub, bullets, chips, col, tc) in enumerate(PROJECTS):
        t0 = 2.6 + i * 0.15
        body = (
            f'<g class="a" {anim("rise", .7, t0)}>' + panel(W, H)
            + f'<g clip-path="url(#pc)"><rect x="0" y="0" width="{W}" height="84" fill="{col}"/></g>'
            + f'<line x1="2" y1="84" x2="{W-6}" y2="84" stroke="{INK}" stroke-width="2"/>'
            + f'<text class="o" x="24" y="34" font-size="10" font-weight="700" fill="{tc}" opacity=".85">{esc(tag)}</text>'
            + f'<text class="o" x="24" y="62" font-size="19" font-weight="700" fill="{tc}">{esc(title)}</text>'
            + f'<text class="f" x="24" y="108" font-size="12" fill="{MUTED}">{esc(sub)}</text>'
        )
        for j, b in enumerate(bullets):
            body += (
                f'<circle cx="28" cy="{132+j*20}" r="3" fill="{col}" stroke="{INK}" stroke-width="1.5"/>'
                f'<text class="f" x="40" y="{136+j*20}" font-size="11.5" fill="{INK}">{esc(b)}</text>'
            )
        x, y = 24, 196
        for c in chips:
            w = len(c) * 6.6 + 18
            if x + w > W - 30:
                x, y = 24, y + 25
            body += (
                f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="21" rx="6" fill="{TINT[col]}" stroke="{INK}" stroke-width="1.5"/>'
                f'<text class="f" x="{x+w/2:.0f}" y="{y+14.5}" font-size="10.5" fill="{INK}" text-anchor="middle">{esc(c)}</text>'
            )
            x += w + 7
        body += "</g>"
        save(f"project-{slug}", svg(W, H, body, ["orb700", "fira"], defs=clip("pc", W, H)))


# ---------- 7. link buttons ----------
LINKS = [("LinkedIn", "shivam076", BLUE, "#fff"), ("Email", "p622133@gmail.com", RED, "#fff"),
         ("Portfolio", "see my work", YELLOW, INK), ("GitHub", "DEV1767", "#2B2F42", "#fff")]


def buttons():
    W, H = 200, 66
    for i, (name, sub, col, tc) in enumerate(LINKS):
        body = (
            f'<g class="a" {anim("rise", .6, 3.4 + i*.1)}>' + panel(W, H, 12, fill=col)
            + f'<text class="o" x="18" y="29" font-size="12.5" font-weight="700" fill="{tc}">{name}</text>'
            + f'<text class="f" x="18" y="47" font-size="10.5" fill="{tc}" opacity=".85">{esc(sub)}</text>'
            + f'<path d="M{W-42} 34h16m-6-6 6 6-6 6" fill="none" stroke="{tc}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></g>'
        )
        save(f"link-{name.lower()}", svg(W, H, body, ["orb700", "fira"]))


if __name__ == "__main__":
    print(f"Rendering for {data['user']}: {TOTAL} contributions, longest streak {longest}, STATIC={STATIC}")
    for fn in (hero, graph, activity, tiles, stack, projects, buttons):
        fn()
