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

# ---------- palette ----------
BG, PANEL, LINE = "#0A0F1E", "#0F1630", "#1B2547"
CYAN, CYAN_DIM = "#00F7FF", "#0E8A94"
TEXT, MUTED = "#E6EDF7", "#8A97B4"
LEVELS = ["#131B38", "#0B4F5A", "#0A8C99", "#19C9D6", "#00F7FF"]

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


def panel(w, h, r=14):
    return f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="{r}" fill="{BG}" stroke="{LINE}"/>'


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

# ---------- 1. hero ----------
TAGLINES = [
    "AI & ML Engineering student at JNNCE, Shivamogga",
    "Building scalable backends with Node.js & MongoDB",
    "Designing secure auth systems with JWT",
    "Exploring RAG, LLMs & Agentic AI",
]


def hero():
    W, H = 800, 250
    rot = ""
    for i, t in enumerate(TAGLINES):
        cursor_x = 66 + len(t) * 9.6 + 4
        rot += (
            f'<g class="l{i+1} a" style="animation:rot 16s {i*4}s infinite both">'
            f'<text class="f" x="40" y="193" font-size="16" fill="{CYAN}">›</text>'
            f'<text class="f" x="62" y="193" font-size="16" fill="{TEXT}">{esc(t)}</text>'
            f'<rect x="{cursor_x:.0f}" y="180" width="8" height="15" fill="{CYAN}" '
            f'style="animation:blink 1s steps(1) infinite"/></g>'
        )
    shine = (
        ""
        if STATIC
        else '<animateTransform attributeName="gradientTransform" type="translate" '
        'from="-420 0" to="900 0" dur="5s" begin="1.6s" repeatCount="indefinite"/>'
    )
    defs = (
        f'<linearGradient id="nm" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="420" y2="0">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".4" stop-color="{CYAN}"/>'
        f'<stop offset=".5" stop-color="#FFFFFF"/><stop offset=".6" stop-color="{CYAN}"/>'
        f'<stop offset="1" stop-color="{CYAN}"/>{shine}</linearGradient>'
        f'<linearGradient id="bm" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{CYAN}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>'
        f'<pattern id="gr" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M32 0H0V32" fill="none" stroke="{LINE}" stroke-width=".6" opacity=".7"/></pattern>'
        f'<clipPath id="cl"><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14"/></clipPath>'
    )
    body = (
        panel(W, H)
        + f'<g clip-path="url(#cl)"><rect width="{W}" height="{H}" fill="url(#gr)"/>'
        + f'<g class="a" style="animation:beam 7s 1.2s infinite linear both"><rect width="160" height="{H}" fill="url(#bm)"/></g></g>'
        + f'<text class="o a" x="40" y="96" font-size="46" font-weight="800" fill="url(#nm)" {anim("rise", .9, .15)}>Shivam Chaudhary</text>'
        + f'<rect class="a" x="40" y="114" width="96" height="3" rx="1.5" fill="{CYAN}" style="transform-box:fill-box;transform-origin:left;animation:draw .7s .8s both cubic-bezier(.2,.8,.2,1)"/>'
        + f'<text class="o a" x="40" y="148" font-size="16" font-weight="700" fill="{CYAN_DIM}" {anim("fade", .8, 1.0)}>Generative AI <tspan class="f">·</tspan> Agents <tspan class="f">·</tspan> Backend</text>'
        + rot
        + f'<circle cx="46" cy="226" r="3.5" fill="{CYAN}"/>'
        + f'<circle class="pulse" cx="46" cy="226" r="3.5" fill="none" stroke="{CYAN}" style="animation:pulse 2s 1.5s infinite both"/>'
        + f'<text class="f a" x="62" y="230" font-size="12.5" fill="{MUTED}" {anim("fade", .8, 1.4)}>Open to backend, full-stack and AI collaborations</text>'
    )
    save("hero", svg(W, H, body, ["orb800", "orb700", "fira"], defs=defs))


# ---------- 2. contribution graph ----------
def graph():
    W, PAD, CELL, GAP = 800, 24, 11, 3.2
    first = DAYS[0][0]
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # back up to Sunday
    pitch = CELL + GAP
    cols = (DAYS[-1][0] - start).days // 7 + 1
    pitch = (W - PAD * 2 + GAP) / cols
    cell = pitch - GAP
    H = 64 + 7 * pitch + 36
    rects, labels, seen = "", "", set()
    for d, c, lv in DAYS:
        col, row = (d - start).days // 7, (d.weekday() + 1) % 7
        x, yy = PAD + col * pitch, 54 + row * pitch
        rects += (
            f'<rect class="a" x="{x:.1f}" y="{yy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.2" fill="{LEVELS[lv]}" '
            f'style="animation:pop .45s {0.5 + col*0.028:.2f}s both"/>'
        )
        if d.day <= 7 and (d.year, d.month) not in seen and row == 0 or (d.day == 1 and (d.year, d.month) not in seen):
            seen.add((d.year, d.month))
            labels += f'<text class="f" x="{x:.1f}" y="46" font-size="10.5" fill="{MUTED}">{d.strftime("%b")}</text>'
    leg_x = W - PAD - 5 * (cell + 4) - 70
    legend = f'<text class="f" x="{leg_x:.0f}" y="{H-14:.0f}" font-size="10.5" fill="{MUTED}">Less</text>'
    for i, col in enumerate(LEVELS):
        legend += f'<rect x="{leg_x+32+i*(cell+4):.0f}" y="{H-23:.0f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.2" fill="{col}"/>'
    legend += f'<text class="f" x="{leg_x+36+5*(cell+4):.0f}" y="{H-14:.0f}" font-size="10.5" fill="{MUTED}">More</text>'
    body = (
        panel(W, H)
        + f'<text class="o" x="{PAD}" y="28" font-size="12" font-weight="700" fill="{CYAN}">Contribution graph</text>'
        + labels + rects + legend
    )
    save("graph", svg(W, round(H), body, ["orb700", "fira"]))


# ---------- 3. activity: stats + monthly bars ----------
def activity():
    W, H = 800, 330
    stats = [
        (TOTAL, "contributions", "last 12 months"),
        (ACTIVE, "active days", "of the last 12 months"),
        (longest, "day streak", "longest run"),
        (BUSIEST[1], "in one day", BUSIEST[0].strftime("%d %b %Y")),
    ]
    body = panel(W, H)
    colw = (W - 48) / 4
    for i, (v, l1, l2) in enumerate(stats):
        x = 28 + i * colw
        body += countup(x, 62, v, "o", 34, CYAN, 0.5 + i * 0.12)
        body += f'<text class="f a" x="{x}" y="86" font-size="12" fill="{TEXT}" {anim("fade", .6, 1.0+i*.1)}>{esc(l1)}</text>'
        body += f'<text class="f a" x="{x}" y="103" font-size="11" fill="{MUTED}" {anim("fade", .6, 1.1+i*.1)}>{esc(l2)}</text>'
    body += f'<line x1="24" y1="124" x2="{W-24}" y2="124" stroke="{LINE}"/>'
    body += f'<text class="o" x="24" y="150" font-size="12" font-weight="700" fill="{CYAN}">Contributions per month</text>'
    base, top = 292, 178
    mx = max(month_totals) or 1
    bw = (W - 48) / 12
    best = month_totals.index(max(month_totals))
    for i, ((yy, mm), t) in enumerate(zip(months, month_totals)):
        x = 24 + i * bw + 8
        h = max(3, (base - top) * t / mx)
        fill = CYAN if i == best else CYAN_DIM
        body += (
            f'<rect class="a" x="{x:.1f}" y="{base-h:.1f}" width="{bw-16:.1f}" height="{h:.1f}" rx="4" fill="{fill}" '
            f'style="transform-box:fill-box;transform-origin:bottom;animation:grow .8s {1.2+i*.07:.2f}s both cubic-bezier(.2,.8,.2,1)"/>'
        )
        lab = dt.date(yy, mm, 1).strftime("%b")
        body += f'<text class="f" x="{x+(bw-16)/2:.1f}" y="{base+20}" font-size="11" fill="{MUTED}" text-anchor="middle">{lab}</text>'
        if i == best:
            body += (
                f'<text class="o a" x="{x+(bw-16)/2:.1f}" y="{base-h-9:.1f}" font-size="14" font-weight="700" fill="{CYAN}" '
                f'text-anchor="middle" {anim("pop", .5, 2.2, ";transform-box:fill-box;transform-origin:center")}>{t}</text>'
            )
    save("activity", svg(W, H, body, ["orb700", "fira"]))


# ---------- 4. three tiles ----------
TILES = [
    ("Freelance", 1, "live production site", ["Web developer at Indalnova", "Maintains their production site"]),
    ("Hackathons", 3, "events entered", ["VeriVox AI, Hack Fest 1.0", "Smart India Hackathon (Internal)", "IGNITRON 2K25"]),
    ("Learning", 4, "topics in progress", ["LangGraph multi-agent flows", "Advanced RAG", "Vector DB optimization", "System design"]),
]


def tiles():
    W, H = 260, 215
    shine = (
        ""
        if STATIC
        else '<g class="a" style="animation:beam 6s 3s infinite linear both"><rect width="70" height="215" fill="url(#ts)" transform="skewX(-14)"/></g>'
    )
    defs = (
        f'<linearGradient id="ts" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="tc"><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14"/></clipPath>'
    )
    for i, (title, n, label, lines) in enumerate(TILES):
        t0 = 1.9 + i * 0.2
        lines_svg = "".join(
            f'<text class="f a" x="22" y="{146+j*18}" font-size="11" fill="{TEXT}" {anim("fade", .5, t0+.9+j*.12)}>{esc(l)}</text>'
            f'<rect x="12" y="{140+j*18}" width="3" height="3" rx="1" fill="{CYAN_DIM}"/>'
            for j, l in enumerate(lines)
        )
        body = (
            f'<g class="a" style="transform-box:fill-box;transform-origin:0 100%;animation:swing 1s {t0-.2:.2f}s both cubic-bezier(.2,.9,.3,1.2)">'
            + panel(W, H)
            + f'<g clip-path="url(#tc)">{shine}</g>'
            + f'<text class="o" x="22" y="34" font-size="13" font-weight="700" fill="{CYAN}">{title}</text>'
            + countup(22, 90, n, "o", 44, TEXT, t0 + 0.3, frames=8, step=0.08)
            + f'<text class="f" x="22" y="112" font-size="11" fill="{MUTED}">{esc(label)}</text>'
            + f'<line x1="22" y1="124" x2="{W-22}" y2="124" stroke="{LINE}"/>'
            + lines_svg
            + "</g>"
        )
        save(f"tile-{title.lower()}", svg(W, H, body, ["orb700", "fira"], defs=defs))


# ---------- 5. tech stack ----------
STACK = [
    ("Backend", ["Node.js", "Express", "FastAPI", "JWT"]),
    ("Databases", ["MongoDB", "Mongoose", "Redis", "Qdrant", "Supabase"]),
    ("AI / ML", ["PyTorch", "LangChain", "LangGraph", "Gemini", "Groq"]),
    ("Languages", ["JavaScript", "TypeScript", "Python", "C"]),
    ("Tools", ["Git", "GitHub", "VS Code", "Postman"]),
]


def stack():
    W, ROW = 800, 42
    H = 56 + len(STACK) * ROW + 6
    body = panel(W, H) + f'<text class="o" x="24" y="34" font-size="12" font-weight="700" fill="{CYAN}">Tech stack</text>'
    n = 0
    for r, (cat, items) in enumerate(STACK):
        y = 56 + r * ROW
        body += f'<text class="o" x="24" y="{y+23}" font-size="11" font-weight="700" fill="{MUTED}">{esc(cat)}</text>'
        x = 150
        for it in items:
            w = len(it) * 7.8 + 24
            body += (
                f'<g class="a" {anim("rise", .5, 0.3+n*.05)}>'
                f'<rect x="{x}" y="{y+4}" width="{w:.0f}" height="28" rx="7" fill="{PANEL}" stroke="{LINE}"/>'
                f'<text class="f" x="{x+w/2:.0f}" y="{y+22}" font-size="13" fill="{TEXT}" text-anchor="middle">{esc(it)}</text></g>'
            )
            x += w + 10
            n += 1
    save("stack", svg(W, H, body, ["orb700", "fira"]))


# ---------- 6. projects ----------
PROJECTS = [
    ("ai-git-rag", "AI & Agentic", "Git RAG", "Agentic GitHub repository assistant",
     ["Repository ingestion and code chunking", "Hybrid retrieval with reranking", "MCP-based tool execution"],
     ["Python", "LangGraph", "LangChain", "MCP", "Qdrant", "FastAPI", "Groq"]),
    ("ai-commander", "AI & Agentic", "AI Commander", "VS Code AI agent for debugging",
     ["Captures terminal errors from your workflow", "Agent gives context-aware debugging help", "Extension backed by Node.js and FastAPI"],
     ["TypeScript", "VS Code API", "Node.js", "Express", "FastAPI", "LangGraph", "MongoDB", "LLM APIs"]),
    ("eventhub", "Backend", "EventHub", "College event management platform",
     ["Built for 1,000+ concurrent users", "Role-based access with JWT auth", "Joi-validated REST APIs, Redis caching"],
     ["Node.js", "Express", "MongoDB", "Mongoose", "Redis", "JWT", "Joi"]),
    ("url-shortener", "Backend", "URL Shortener", "Backend service with user accounts",
     ["JWT-based authentication and authorization", "MongoDB persistence", "Redirects to the original URL"],
     ["Node.js", "Express", "MongoDB", "JWT"]),
]


def projects():
    W, H = 400, 238
    for i, (slug, tag, title, sub, bullets, chips) in enumerate(PROJECTS):
        t0 = 2.6 + i * 0.15
        body = (
            f'<g class="a" {anim("rise", .7, t0)}>' + panel(W, H)
            + f'<text class="o" x="24" y="32" font-size="10" font-weight="700" fill="{MUTED}">{esc(tag)}</text>'
            + f'<text class="o" x="24" y="60" font-size="18" font-weight="700" fill="{CYAN}">{esc(title)}</text>'
            + f'<text class="f" x="24" y="80" font-size="12" fill="{MUTED}">{esc(sub)}</text>'
        )
        for j, b in enumerate(bullets):
            body += (
                f'<text class="f" x="40" y="{110+j*21}" font-size="11.5" fill="{TEXT}">{esc(b)}</text>'
                f'<text class="f" x="24" y="{110+j*21}" font-size="11.5" fill="{CYAN}">›</text>'
            )
        x, y = 24, 180
        for c in chips:
            w = len(c) * 6.6 + 18
            if x + w > W - 24:
                x, y = 24, y + 27
            body += (
                f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="22" rx="6" fill="{PANEL}" stroke="{LINE}"/>'
                f'<text class="f" x="{x+w/2:.0f}" y="{y+15}" font-size="10.5" fill="#5CCDD6" text-anchor="middle">{esc(c)}</text>'
            )
            x += w + 7
        body += "</g>"
        save(f"project-{slug}", svg(W, H, body, ["orb700", "fira"]))


# ---------- 7. link buttons ----------
LINKS = [("LinkedIn", "shivam076"), ("Email", "p622133@gmail.com"), ("Portfolio", "see my work"), ("GitHub", "DEV1767")]


def buttons():
    W, H = 196, 56
    for i, (name, sub) in enumerate(LINKS):
        body = (
            f'<g class="a" {anim("rise", .6, 3.4 + i*.1)}>' + panel(W, H, 12)
            + f'<text class="o" x="18" y="24" font-size="12" font-weight="700" fill="{CYAN}">{name}</text>'
            + f'<text class="f" x="18" y="42" font-size="10.5" fill="{MUTED}">{esc(sub)}</text>'
            + f'<path d="M{W-34} 28h16m-6-6 6 6-6 6" fill="none" stroke="{CYAN_DIM}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></g>'
        )
        save(f"link-{name.lower()}", svg(W, H, body, ["orb700", "fira"]))


if __name__ == "__main__":
    print(f"Rendering for {data['user']}: {TOTAL} contributions, streak {current}/{longest}, STATIC={STATIC}")
    for fn in (hero, graph, activity, tiles, stack, projects, buttons):
        fn()
