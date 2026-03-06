#!/usr/bin/env python3
# ============================================================
#   █████╗ ██╗    ██╗    ███████╗██████╗
#  ██╔══██╗██║    ██║    ██╔════╝██╔══██╗
#  ███████║██║ █╗ ██║    █████╗  ██████╔╝
#  ██╔══██║██║███╗██║    ██╔══╝  ██╔══██╗
#  ██║  ██║╚███╔███╔╝    ██║     ██████╔╝
#  ╚═╝  ╚═╝ ╚══╝╚══╝     ╚═╝     ╚═════╝
#  EXTRACTOR  v1.0  |  by AW (ahmed-awad26)
# ============================================================

import sys
import os
import json
import csv
import time
import re
import traceback
from datetime import datetime
from pathlib import Path

# ── Rich TUI ──────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich.rule import Rule
    from rich.style import Style
except ImportError:
    print("[!] 'rich' not installed. Run: pip install rich")
    sys.exit(1)

# ── facebook-scraper ──────────────────────────────────────
try:
    from facebook_scraper import get_posts, get_profile
except ImportError:
    print("[!] 'facebook-scraper' not installed. Run: pip install facebook-scraper")
    sys.exit(1)

# ── requests / PIL ────────────────────────────────────────
try:
    import requests
    from requests.exceptions import RequestException
except ImportError:
    print("[!] 'requests' not installed. Run: pip install requests")
    sys.exit(1)

console = Console()

# ═══════════════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════════════
BANNER = """
[bold cyan]  ╔══════════════════════════════════════════════════╗[/]
[bold cyan]  ║[/]  [bold white]█████[/][bold blue]╗[/] [bold white]██╗[/]    [bold white]██╗    ███████[/][bold blue]╗[/][bold white]██████[/][bold blue]╗[/]              [bold cyan]║[/]
[bold cyan]  ║[/] [bold white]██[/][bold blue]╔══[/][bold white]██[/][bold blue]╗[/][bold white]██║[/]    [bold white]██║    ██[/][bold blue]╔════╝[/][bold white]██[/][bold blue]╔══[/][bold white]██[/][bold blue]╗[/]             [bold cyan]║[/]
[bold cyan]  ║[/] [bold white]███████║██║ █╗ ██║    █████[/][bold blue]╗  [/][bold white]██████[/][bold blue]╔╝[/]             [bold cyan]║[/]
[bold cyan]  ║[/] [bold white]██[/][bold blue]╔══[/][bold white]██║██║███╗██║    ██[/][bold blue]╔══╝  [/][bold white]██[/][bold blue]╔══[/][bold white]██[/][bold blue]╗[/]             [bold cyan]║[/]
[bold cyan]  ║[/] [bold white]██║  ██║[/][bold blue]╚[/][bold white]███[/][bold blue]╔[/][bold white]███[/][bold blue]╔╝    [/][bold white]██║     ██████[/][bold blue]╔╝[/]             [bold cyan]║[/]
[bold cyan]  ║[/] [bold blue]╚═╝  ╚═╝ ╚══╝╚══╝     ╚═╝     ╚═════╝[/]              [bold cyan]║[/]
[bold cyan]  ║[/]    [bold yellow]Facebook Post Extractor[/]  [dim]v1.0[/]  [bold magenta]by AW[/]          [bold cyan]║[/]
[bold cyan]  ╚══════════════════════════════════════════════════╝[/]
"""

# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════

def clear():
    os.system("clear")

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def safe_str(val):
    if val is None:
        return ""
    return str(val)

def extract_profile_id(url_or_id: str) -> str:
    """Extract profile ID or username from URL."""
    url_or_id = url_or_id.strip().rstrip("/")
    patterns = [
        r"facebook\.com/profile\.php\?id=(\d+)",
        r"facebook\.com/([^/?]+)",
        r"fb\.com/([^/?]+)",
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    return url_or_id  # assume it's already a username/id

def download_image(url: str, out_path: str) -> bool:
    """Download an image to disk. Returns True on success."""
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

def get_video_thumbnail(post: dict, img_dir: str) -> str:
    """Try to grab video thumbnail URL from a post."""
    thumb = post.get("thumbnail") or post.get("image") or ""
    return thumb

def format_date(dt) -> str:
    if dt is None:
        return "Unknown date"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)

def visibility_label(v: str) -> str:
    m = {"PUBLIC": "🌍 Public", "FRIENDS": "👥 Friends Only",
         "ONLY_ME": "🔒 Only Me", "CUSTOM": "⚙️  Custom"}
    return m.get(str(v).upper(), f"❓ {v}")

# ═══════════════════════════════════════════════════════════
#  SCRAPER
# ═══════════════════════════════════════════════════════════

class FacebookScraper:
    def __init__(self, cookies_path: str | None = None):
        self.cookies_path = cookies_path
        self.cookies = None
        if cookies_path and os.path.exists(cookies_path):
            self._load_cookies(cookies_path)

    def _load_cookies(self, path: str):
        try:
            with open(path) as f:
                self.cookies = json.load(f)
            console.print(f"[green]✔ Cookies loaded from {path}[/]")
        except Exception as e:
            console.print(f"[red]✘ Failed to load cookies: {e}[/]")
            self.cookies = None

    def fetch_posts(self, profile_id: str, max_posts: int,
                    visibility_filter: str | None,
                    progress_callback=None) -> list[dict]:
        """
        Fetch posts from a profile.
        visibility_filter: 'PUBLIC' | 'FRIENDS' | 'ONLY_ME' | None (all)
        """
        options = {
            "posts_per_page": 10,
            "timeout": 60,
        }
        if self.cookies:
            options["cookies"] = self.cookies

        posts = []
        fetched = 0

        try:
            for post in get_posts(profile_id, pages=max_posts // 10 + 2,
                                   options=options):
                raw_vis = str(post.get("privacy", "") or "").upper()

                # Apply visibility filter
                if visibility_filter and visibility_filter != "ALL":
                    if raw_vis and raw_vis != visibility_filter.upper():
                        continue

                # Enrich post data
                enriched = self._enrich_post(post)
                posts.append(enriched)
                fetched += 1

                if progress_callback:
                    progress_callback(fetched)

                if fetched >= max_posts:
                    break

        except Exception as e:
            console.print(f"\n[yellow]⚠  Scraper stopped: {e}[/]")

        return posts

    def _enrich_post(self, post: dict) -> dict:
        """Normalize and enrich a raw post dict."""
        text = safe_str(post.get("text") or post.get("post_text") or "")
        shared_text = safe_str(post.get("shared_text") or "")
        shared_url = safe_str(post.get("shared_post_url") or "")

        return {
            "post_id":      safe_str(post.get("post_id") or post.get("id") or ""),
            "post_url":     safe_str(post.get("post_url") or ""),
            "date":         post.get("time"),
            "date_str":     format_date(post.get("time")),
            "text":         text,
            "shared_text":  shared_text,
            "shared_url":   shared_url,
            "is_shared":    bool(shared_url or shared_text),
            "images":       post.get("images") or [],
            "image":        safe_str(post.get("image") or ""),
            "video_url":    safe_str(post.get("video") or post.get("video_url") or ""),
            "is_video":     bool(post.get("video") or post.get("video_url")),
            "thumbnail":    safe_str(post.get("thumbnail") or ""),
            "likes":        post.get("likes") or 0,
            "comments":     post.get("comments") or 0,
            "shares":       post.get("shares") or 0,
            "privacy":      safe_str(post.get("privacy") or "PUBLIC"),
            "reactions":    post.get("reactions") or {},
        }

# ═══════════════════════════════════════════════════════════
#  EXPORTERS
# ═══════════════════════════════════════════════════════════

def export_links(posts: list[dict], out_dir: str) -> str:
    path = os.path.join(out_dir, f"posts_links_{ts()}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# AW FB Extractor — Post Links\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total posts: {len(posts)}\n\n")
        for i, p in enumerate(posts, 1):
            f.write(f"[{i:03d}] {p['date_str']} | {p['privacy']}\n")
            f.write(f"      URL: {p['post_url']}\n")
            if p["is_shared"] and p["shared_url"]:
                f.write(f"      SHARED FROM: {p['shared_url']}\n")
            if p["is_video"] and p["video_url"]:
                f.write(f"      VIDEO: {p['video_url']}\n")
            f.write("\n")
    return path


def export_json(posts: list[dict], out_dir: str) -> str:
    path = os.path.join(out_dir, f"posts_{ts()}.json")
    data = {
        "meta": {
            "generated": datetime.now().isoformat(),
            "total_posts": len(posts),
            "tool": "AW FB Extractor v1.0"
        },
        "posts": posts
    }

    def default_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=default_serial)
    return path


def export_csv(posts: list[dict], out_dir: str) -> str:
    path = os.path.join(out_dir, f"posts_{ts()}.csv")
    fields = ["post_id", "date_str", "privacy", "text", "shared_text",
              "shared_url", "is_shared", "is_video", "video_url",
              "likes", "comments", "shares", "post_url"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for p in posts:
            row = {k: p.get(k, "") for k in fields}
            row["text"] = row["text"][:500]  # truncate long text
            writer.writerow(row)
    return path


def export_html(posts: list[dict], out_dir: str, profile_id: str,
                img_dir: str | None = None) -> str:
    path = os.path.join(out_dir, f"posts_{ts()}.html")

    def escape_html(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                      .replace(">", "&gt;").replace('"', "&quot;"))

    def post_card(p: dict, idx: int) -> str:
        privacy_colors = {
            "PUBLIC": "#4caf50", "FRIENDS": "#2196f3",
            "ONLY_ME": "#ff9800", "CUSTOM": "#9c27b0"
        }
        prv = str(p.get("privacy", "PUBLIC")).upper()
        prv_color = privacy_colors.get(prv, "#888")

        # Shared badge
        shared_badge = ""
        if p["is_shared"]:
            shared_badge = f"""
            <div class="shared-block">
              <div class="shared-header">🔁 Shared from:
                <a href="{escape_html(p['shared_url'])}" target="_blank">{escape_html(p['shared_url'])[:60]}…</a>
              </div>
              <div class="shared-text">{escape_html(p['shared_text'][:800])}</div>
            </div>"""

        # Video block
        video_block = ""
        if p["is_video"]:
            thumb = p.get("thumbnail") or p.get("image") or ""
            thumb_html = f'<img class="video-thumb" src="{escape_html(thumb)}" alt="Video thumbnail" />' if thumb else ""
            video_block = f"""
            <div class="video-block">
              {thumb_html}
              <div class="video-meta">
                🎬 <strong>Video Post</strong><br>
                <a href="{escape_html(p['video_url'])}" target="_blank" class="btn-link">▶ Watch Video</a>
              </div>
            </div>"""

        # Images
        imgs_html = ""
        for img_url in (p.get("images") or [])[:4]:
            imgs_html += f'<a href="{escape_html(img_url)}" target="_blank"><img class="post-img" src="{escape_html(img_url)}" loading="lazy" /></a>'

        # Stats
        stats = f"""
          <div class="stats">
            <span>👍 {p.get('likes', 0)}</span>
            <span>💬 {p.get('comments', 0)}</span>
            <span>🔁 {p.get('shares', 0)}</span>
          </div>"""

        return f"""
    <div class="post-card" id="post-{idx}">
      <div class="post-header">
        <span class="post-num">#{idx:03d}</span>
        <span class="post-date">📅 {escape_html(p['date_str'])}</span>
        <span class="privacy-badge" style="background:{prv_color}">{escape_html(prv)}</span>
        <a class="post-link-btn" href="{escape_html(p['post_url'])}" target="_blank">🔗 Open Post</a>
      </div>
      <div class="post-text">{escape_html(p['text'][:1500])}</div>
      {shared_badge}
      {video_block}
      {"<div class='post-images'>" + imgs_html + "</div>" if imgs_html else ""}
      {stats}
    </div>"""

    cards_html = "\n".join(post_card(p, i) for i, p in enumerate(posts, 1))
    pub_count  = sum(1 for p in posts if str(p.get("privacy","")).upper() == "PUBLIC")
    fri_count  = sum(1 for p in posts if str(p.get("privacy","")).upper() == "FRIENDS")
    prv_count  = sum(1 for p in posts if str(p.get("privacy","")).upper() == "ONLY_ME")
    vid_count  = sum(1 for p in posts if p.get("is_video"))
    sh_count   = sum(1 for p in posts if p.get("is_shared"))

    html = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>AW FB Extractor — {escape_html(profile_id)}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');

  :root {{
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #1c2128;
    --border: #30363d;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --accent: #1877f2;
    --accent-glow: rgba(24,119,242,0.25);
    --green: #4caf50;
    --yellow: #e3b341;
    --red: #f85149;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    padding-bottom: 60px;
  }}

  /* ── HEADER ── */
  .hero {{
    background: linear-gradient(135deg, #0d1117 0%, #0a1628 50%, #0d1117 100%);
    border-bottom: 1px solid var(--border);
    padding: 48px 32px 32px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }}
  .hero::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 300px;
    background: radial-gradient(ellipse, rgba(24,119,242,0.15), transparent 70%);
    pointer-events: none;
  }}
  .hero-badge {{
    display: inline-block;
    background: var(--accent);
    color: #fff;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 2px;
    margin-bottom: 16px;
  }}
  .hero h1 {{
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #e6edf3, #1877f2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
  }}
  .hero .profile-id {{
    font-family: 'JetBrains Mono', monospace;
    color: var(--accent);
    font-size: 1rem;
    margin-bottom: 6px;
  }}
  .hero .meta {{
    color: var(--text-dim);
    font-size: 0.85rem;
  }}

  /* ── STATS BAR ── */
  .stats-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    justify-content: center;
    padding: 24px 32px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }}
  .stat-chip {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 20px;
    text-align: center;
    min-width: 110px;
  }}
  .stat-chip .val {{
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    display: block;
  }}
  .stat-chip .lbl {{
    font-size: 0.72rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
  }}

  /* ── TOOLBAR ── */
  .toolbar {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 16px 32px;
    align-items: center;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }}
  .toolbar input {{
    flex: 1;
    min-width: 200px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    padding: 8px 14px;
    font-size: 0.9rem;
    outline: none;
  }}
  .toolbar input:focus {{
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }}
  .filter-btn {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text-dim);
    border-radius: 6px;
    padding: 7px 14px;
    cursor: pointer;
    font-size: 0.82rem;
    transition: all .2s;
  }}
  .filter-btn:hover, .filter-btn.active {{
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-glow);
  }}

  /* ── LAYOUT ── */
  .container {{
    max-width: 900px;
    margin: 0 auto;
    padding: 32px 16px;
  }}
  .posts-count {{
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-bottom: 20px;
    font-family: 'JetBrains Mono', monospace;
  }}

  /* ── POST CARD ── */
  .post-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    transition: border-color .2s, transform .1s;
  }}
  .post-card:hover {{
    border-color: var(--accent);
    transform: translateY(-1px);
  }}
  .post-header {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
  }}
  .post-num {{
    font-family: 'JetBrains Mono', monospace;
    color: var(--accent);
    font-weight: 700;
    font-size: 0.85rem;
  }}
  .post-date {{
    color: var(--text-dim);
    font-size: 0.82rem;
  }}
  .privacy-badge {{
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    color: #fff;
    letter-spacing: 0.5px;
  }}
  .post-link-btn {{
    margin-left: auto;
    background: var(--accent);
    color: #fff;
    text-decoration: none;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    transition: opacity .2s;
  }}
  .post-link-btn:hover {{ opacity: 0.85; }}

  .post-text {{
    color: var(--text);
    font-size: 0.92rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
    margin-bottom: 12px;
  }}

  /* Shared */
  .shared-block {{
    background: var(--surface2);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 12px 0;
  }}
  .shared-header {{
    font-size: 0.8rem;
    color: var(--text-dim);
    margin-bottom: 6px;
  }}
  .shared-header a {{ color: var(--accent); text-decoration: none; }}
  .shared-text {{
    color: var(--text);
    font-size: 0.88rem;
    line-height: 1.5;
    white-space: pre-wrap;
  }}

  /* Video */
  .video-block {{
    display: flex;
    align-items: center;
    gap: 16px;
    background: #0a0f1a;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 14px;
    margin: 12px 0;
  }}
  .video-thumb {{
    width: 120px;
    height: 68px;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid var(--border);
  }}
  .video-meta {{ font-size: 0.88rem; }}
  .btn-link {{
    display: inline-block;
    background: #e53935;
    color: #fff;
    text-decoration: none;
    padding: 5px 14px;
    border-radius: 6px;
    font-size: 0.8rem;
    margin-top: 6px;
  }}
  .btn-link:hover {{ opacity: 0.85; }}

  /* Images */
  .post-images {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 10px 0;
  }}
  .post-img {{
    width: 130px;
    height: 90px;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid var(--border);
    cursor: pointer;
  }}

  /* Stats */
  .stats {{
    display: flex;
    gap: 16px;
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--border);
  }}
  .stats span {{
    color: var(--text-dim);
    font-size: 0.82rem;
  }}

  /* Hidden */
  .post-card.hidden {{ display: none; }}

  /* Footer */
  .footer {{
    text-align: center;
    padding: 40px;
    color: var(--text-dim);
    font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    border-top: 1px solid var(--border);
    margin-top: 40px;
  }}

  @media (max-width: 600px) {{
    .hero h1 {{ font-size: 1.6rem; }}
    .stats-bar {{ gap: 8px; }}
    .toolbar {{ padding: 12px 16px; }}
  }}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-badge">AW FB EXTRACTOR v1.0</div>
  <h1>Facebook Post Archive</h1>
  <div class="profile-id">@{escape_html(profile_id)}</div>
  <div class="meta">Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')} &nbsp;|&nbsp; {len(posts)} posts extracted</div>
</div>

<div class="stats-bar">
  <div class="stat-chip"><span class="val">{len(posts)}</span><span class="lbl">Total Posts</span></div>
  <div class="stat-chip"><span class="val">{pub_count}</span><span class="lbl">Public</span></div>
  <div class="stat-chip"><span class="val">{fri_count}</span><span class="lbl">Friends Only</span></div>
  <div class="stat-chip"><span class="val">{prv_count}</span><span class="lbl">Only Me</span></div>
  <div class="stat-chip"><span class="val">{vid_count}</span><span class="lbl">Videos</span></div>
  <div class="stat-chip"><span class="val">{sh_count}</span><span class="lbl">Shared</span></div>
</div>

<div class="toolbar">
  <input type="text" id="search" placeholder="🔍 Search posts…" oninput="filterPosts()" />
  <button class="filter-btn active" onclick="setFilter('all', this)">All</button>
  <button class="filter-btn" onclick="setFilter('PUBLIC', this)">🌍 Public</button>
  <button class="filter-btn" onclick="setFilter('FRIENDS', this)">👥 Friends</button>
  <button class="filter-btn" onclick="setFilter('ONLY_ME', this)">🔒 Only Me</button>
  <button class="filter-btn" onclick="setFilter('video', this)">🎬 Videos</button>
  <button class="filter-btn" onclick="setFilter('shared', this)">🔁 Shared</button>
</div>

<div class="container">
  <div class="posts-count" id="posts-count">Showing {len(posts)} posts</div>
  <div id="posts-container">
    {cards_html}
  </div>
</div>

<div class="footer">
  AW FB Extractor v1.0 &nbsp;·&nbsp; github.com/ahmed-awad26 &nbsp;·&nbsp; {datetime.now().year}
</div>

<script>
  let currentFilter = 'all';

  function setFilter(f, btn) {{
    currentFilter = f;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterPosts();
  }}

  function filterPosts() {{
    const q = document.getElementById('search').value.toLowerCase();
    const cards = document.querySelectorAll('.post-card');
    let visible = 0;

    cards.forEach(card => {{
      const text = card.innerText.toLowerCase();
      const prv  = card.querySelector('.privacy-badge')?.textContent || '';
      const isVideo  = card.querySelector('.video-block') !== null;
      const isShared = card.querySelector('.shared-block') !== null;

      let show = text.includes(q);
      if (show && currentFilter !== 'all') {{
        if (currentFilter === 'video')  show = isVideo;
        else if (currentFilter === 'shared') show = isShared;
        else show = prv.includes(currentFilter);
      }}

      card.classList.toggle('hidden', !show);
      if (show) visible++;
    }});
    document.getElementById('posts-count').textContent = `Showing ${{visible}} of ${{cards.length}} posts`;
  }}
</script>

</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def export_pdf(posts: list[dict], out_dir: str, profile_id: str) -> str:
    """Generate a formatted PDF report."""
    try:
        from fpdf import FPDF, XPos, YPos
    except ImportError:
        console.print("[yellow]⚠  fpdf2 not installed. Skipping PDF.[/]")
        return ""

    path = os.path.join(out_dir, f"posts_{ts()}.pdf")

    class AWPDF(FPDF):
        def header(self):
            self.set_fill_color(13, 17, 23)
            self.rect(0, 0, 210, 18, "F")
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(24, 119, 242)
            self.cell(0, 18, f"AW FB Extractor  |  @{profile_id}",
                      new_x=XPos.LEFT, new_y=YPos.NEXT, align="C")
            self.set_text_color(200, 200, 200)

        def footer(self):
            self.set_y(-13)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 110, 120)
            self.cell(0, 10,
                      f"AW FB Extractor v1.0  |  Page {self.page_no()}  |  github.com/ahmed-awad26",
                      align="C")

    pdf = AWPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    # ── Cover page stats ──
    pdf.set_fill_color(22, 27, 34)
    pdf.set_draw_color(48, 54, 61)

    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(230, 237, 243)
    pdf.ln(10)
    pdf.cell(0, 12, "Facebook Post Archive", new_x=XPos.LEFT, new_y=YPos.NEXT, align="C")

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(24, 119, 242)
    pdf.cell(0, 8, f"@{profile_id}", new_x=XPos.LEFT, new_y=YPos.NEXT, align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(139, 148, 158)
    pdf.cell(0, 6,
             f"Generated: {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}",
             new_x=XPos.LEFT, new_y=YPos.NEXT, align="C")
    pdf.ln(8)

    # Stats row
    stats = [
        ("TOTAL", len(posts)),
        ("PUBLIC",  sum(1 for p in posts if p.get("privacy","").upper()=="PUBLIC")),
        ("FRIENDS", sum(1 for p in posts if p.get("privacy","").upper()=="FRIENDS")),
        ("ONLY ME", sum(1 for p in posts if p.get("privacy","").upper()=="ONLY_ME")),
        ("VIDEOS",  sum(1 for p in posts if p.get("is_video"))),
        ("SHARED",  sum(1 for p in posts if p.get("is_shared"))),
    ]
    col_w = 30
    start_x = (210 - len(stats)*col_w) / 2
    pdf.set_x(start_x)
    for label, val in stats:
        pdf.set_fill_color(28, 33, 40)
        pdf.set_draw_color(48, 54, 61)
        pdf.cell(col_w - 2, 16, "", border=1, fill=True)
        pdf.set_x(pdf.get_x() - (col_w - 2))
        y0 = pdf.get_y()
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(24, 119, 242)
        pdf.set_xy(pdf.get_x(), y0 + 1)
        pdf.cell(col_w - 2, 7, str(val), align="C",
                 new_x=XPos.RIGHT, new_y=YPos.LAST)
        pdf.set_xy(pdf.get_x() - (col_w - 2), y0 + 8)
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(139, 148, 158)
        pdf.cell(col_w - 2, 5, label, align="C",
                 new_x=XPos.RIGHT, new_y=YPos.LAST)
        pdf.set_xy(pdf.get_x() + 2, y0)

    pdf.ln(22)

    # ── Posts ──
    for i, p in enumerate(posts, 1):
        prv = str(p.get("privacy", "PUBLIC")).upper()
        prv_colors = {
            "PUBLIC":   (76, 175, 80),
            "FRIENDS":  (33, 150, 243),
            "ONLY_ME":  (255, 152, 0),
        }
        prv_rgb = prv_colors.get(prv, (150, 150, 150))

        # Card background
        y_start = pdf.get_y()
        pdf.set_fill_color(22, 27, 34)
        pdf.set_draw_color(48, 54, 61)

        # Header strip
        pdf.set_fill_color(*prv_rgb)
        pdf.cell(0, 1.5, "", new_x=XPos.LEFT, new_y=YPos.NEXT, fill=True)
        pdf.set_fill_color(22, 27, 34)

        # Post header info
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*prv_rgb)
        pdf.cell(12, 6, f"#{i:03d}", new_x=XPos.RIGHT)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(139, 148, 158)
        pdf.cell(60, 6, f"  {p['date_str']}", new_x=XPos.RIGHT)
        pdf.cell(28, 6, f"  [{prv}]", new_x=XPos.RIGHT)
        if p.get("post_url"):
            pdf.set_font("Helvetica", "U", 7.5)
            pdf.set_text_color(24, 119, 242)
            pdf.cell(0, 6, "Open Post →", new_x=XPos.LEFT, new_y=YPos.NEXT,
                     link=p["post_url"])
        else:
            pdf.ln(6)

        # Post text
        text = p.get("text", "").strip()
        if text:
            # Replace non-latin chars that FPDF can't render with safe fallback
            safe_text = text.encode("latin-1", errors="replace").decode("latin-1")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(200, 207, 215)
            pdf.set_x(pdf.l_margin + 2)
            pdf.multi_cell(0, 5, safe_text[:800] + ("…" if len(text) > 800 else ""),
                           new_x=XPos.LEFT)
            pdf.ln(2)

        # Shared
        if p.get("is_shared"):
            pdf.set_fill_color(16, 20, 28)
            pdf.set_draw_color(24, 119, 242)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(24, 119, 242)
            pdf.cell(0, 5, "  Shared from:", new_x=XPos.LEFT, new_y=YPos.NEXT,
                     fill=True, border="L")
            if p.get("shared_url"):
                pdf.set_font("Helvetica", "U", 7.5)
                pdf.cell(0, 4, f"  {p['shared_url'][:80]}",
                         new_x=XPos.LEFT, new_y=YPos.NEXT,
                         link=p["shared_url"])
            shared_t = (p.get("shared_text") or "").strip()
            if shared_t:
                safe_st = shared_t.encode("latin-1", errors="replace").decode("latin-1")
                pdf.set_font("Helvetica", "", 8.5)
                pdf.set_text_color(170, 177, 185)
                pdf.set_x(pdf.l_margin + 4)
                pdf.multi_cell(0, 4.5, safe_st[:400])
            pdf.ln(2)

        # Video
        if p.get("is_video"):
            pdf.set_fill_color(10, 15, 26)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(229, 57, 53)
            pdf.cell(0, 6, "  🎬 Video Post", new_x=XPos.LEFT, new_y=YPos.NEXT,
                     fill=True, border=0)
            if p.get("video_url"):
                pdf.set_font("Helvetica", "U", 7.5)
                pdf.set_text_color(24, 119, 242)
                pdf.cell(0, 5, f"  Watch: {p['video_url'][:80]}",
                         new_x=XPos.LEFT, new_y=YPos.NEXT,
                         link=p["video_url"])
            pdf.ln(2)

        # Stats
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(100, 110, 120)
        pdf.cell(0, 5,
                 f"  👍 {p.get('likes',0)}   💬 {p.get('comments',0)}   🔁 {p.get('shares',0)}",
                 new_x=XPos.LEFT, new_y=YPos.NEXT)

        # Bottom divider
        pdf.set_draw_color(40, 47, 55)
        pdf.line(pdf.l_margin, pdf.get_y() + 1, 210 - pdf.r_margin, pdf.get_y() + 1)
        pdf.ln(5)

    pdf.output(path)
    return path


def export_markdown(posts: list[dict], out_dir: str, profile_id: str) -> str:
    path = os.path.join(out_dir, f"posts_{ts()}.md")
    lines = [
        f"# Facebook Post Archive — @{profile_id}",
        f"> Generated by **AW FB Extractor v1.0** on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> Total posts: **{len(posts)}**",
        "",
        "---",
        ""
    ]
    for i, p in enumerate(posts, 1):
        lines += [
            f"## Post #{i:03d}",
            f"- **Date:** {p['date_str']}",
            f"- **Privacy:** {p['privacy']}",
            f"- **Link:** [{p['post_url']}]({p['post_url']})",
            "",
            p.get("text", "").strip(),
            ""
        ]
        if p.get("is_shared"):
            lines += [
                "> **🔁 Shared from:**",
                f"> {p.get('shared_url', '')}",
                f"> {p.get('shared_text', '')[:500]}",
                ""
            ]
        if p.get("is_video"):
            lines += [
                f"**🎬 Video:** [{p.get('video_url','')}]({p.get('video_url','')})",
                ""
            ]
        stats_line = f"👍 {p.get('likes',0)}  💬 {p.get('comments',0)}  🔁 {p.get('shares',0)}"
        lines += [stats_line, "", "---", ""]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path

# ═══════════════════════════════════════════════════════════
#  COOKIES HELPER
# ═══════════════════════════════════════════════════════════

def guide_cookies():
    console.print(Panel(
        "[bold white]How to export your Facebook cookies:[/]\n\n"
        "[cyan]1.[/] Install [bold]'EditThisCookie'[/] or [bold]'Cookie-Editor'[/] extension in Chrome\n"
        "[cyan]2.[/] Log in to [bold]facebook.com[/]\n"
        "[cyan]3.[/] Open the extension → Export as [bold]JSON[/]\n"
        "[cyan]4.[/] Save the file anywhere (e.g. ~/fb_cookies.json)\n"
        "[cyan]5.[/] Enter the path when prompted\n\n"
        "[dim]Without cookies: only PUBLIC posts are visible.[/]",
        title="[bold blue]🍪 Cookie Setup Guide[/]",
        border_style="blue"
    ))
    input("\nPress Enter to continue…")

# ═══════════════════════════════════════════════════════════
#  MAIN UI
# ═══════════════════════════════════════════════════════════

def choose_export_formats() -> list[str]:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan", width=4)
    table.add_column("Format", style="white")
    table.add_column("Description", style="dim")

    formats = [
        ("1", "Links (.txt)",     "Raw list of post URLs"),
        ("2", "HTML",             "Full interactive web archive"),
        ("3", "PDF",              "Formatted printable report"),
        ("4", "JSON",             "Machine-readable data"),
        ("5", "CSV",              "Spreadsheet-compatible"),
        ("6", "Markdown (.md)",   "Clean markdown file"),
        ("7", "ALL",              "Export all formats at once"),
    ]
    for k, name, desc in formats:
        table.add_row(f"[{k}]", name, desc)

    console.print(Panel(table, title="[bold yellow]📤 Export Format[/]", border_style="yellow"))
    raw = Prompt.ask("[bold]Choose formats[/] [dim](e.g. 1,2,3 or 7 for all)[/]", default="7")
    chosen = [x.strip() for x in raw.split(",")]

    all_keys = {"1": "links", "2": "html", "3": "pdf",
                "4": "json", "5": "csv", "6": "md"}

    if "7" in chosen:
        return list(all_keys.values())
    result = []
    for k in chosen:
        if k in all_keys:
            result.append(all_keys[k])
    return result or ["html", "links"]


def choose_visibility() -> str:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan", width=4)
    table.add_column("Filter", style="white")
    table.add_column("Note", style="dim")

    opts = [
        ("1", "ALL posts",       "No filter — grab everything"),
        ("2", "PUBLIC only",     "Works without login"),
        ("3", "FRIENDS only",    "Requires cookies"),
        ("4", "ONLY ME",         "Requires cookies (your own account)"),
    ]
    for k, name, note in opts:
        table.add_row(f"[{k}]", name, note)

    console.print(Panel(table, title="[bold magenta]🔍 Visibility Filter[/]", border_style="magenta"))
    choice = Prompt.ask("[bold]Select[/]", choices=["1","2","3","4"], default="1")
    return {"1": "ALL", "2": "PUBLIC", "3": "FRIENDS", "4": "ONLY_ME"}[choice]


def run():
    clear()
    console.print(BANNER)
    console.print(Rule(style="dim"))

    # ── Step 1: Profile ──
    console.print("\n[bold cyan]Step 1/4  →  Target Profile[/]")
    profile_input = Prompt.ask(
        "[bold]Facebook profile URL or username[/]\n"
        "[dim]  e.g. facebook.com/zuck  OR  zuck  OR  profile.php?id=4[/]\n  ❯"
    )
    profile_id = extract_profile_id(profile_input)
    console.print(f"[green]✔ Profile ID:[/] [bold]{profile_id}[/]\n")

    # ── Step 2: Cookies ──
    console.print("[bold cyan]Step 2/4  →  Authentication (optional)[/]")
    console.print("[dim]Cookies let you access FRIENDS/ONLY ME posts.[/]")
    use_cookies = Confirm.ask("Use cookies?", default=False)
    cookies_path = None
    if use_cookies:
        console.print("")
        guide_cookies()
        cookies_path = Prompt.ask(
            "[bold]Path to cookies JSON[/] [dim](e.g. /sdcard/fb_cookies.json)[/]",
            default="fb_cookies.json"
        )

    # ── Step 3: Visibility filter ──
    console.print("\n[bold cyan]Step 3/4  →  Visibility Filter[/]")
    visibility = choose_visibility()

    # ── Step 4: Export ──
    console.print("\n[bold cyan]Step 4/4  →  Export Options[/]")
    max_posts = int(Prompt.ask("[bold]Max posts to fetch[/] [dim](0 = unlimited)[/]", default="50"))
    if max_posts == 0:
        max_posts = 99999
    formats = choose_export_formats()

    # Output directory
    out_dir = Prompt.ask(
        "\n[bold]Output directory[/]",
        default=os.path.join(os.path.expanduser("~"), "fb_exports")
    )
    os.makedirs(out_dir, exist_ok=True)
    console.print(f"[green]✔ Output:[/] {out_dir}\n")

    # ── Scraping ──
    console.print(Rule("[bold blue]Scraping Posts[/]"))
    scraper = FacebookScraper(cookies_path=cookies_path)

    posts = []
    with Progress(
        SpinnerColumn(style="bold cyan"),
        TextColumn("[bold cyan]{task.description}[/]"),
        BarColumn(style="cyan"),
        TextColumn("[bold yellow]{task.fields[count]}[/] posts"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Fetching posts from @{profile_id}…",
            total=max_posts,
            count=0
        )

        def on_progress(n):
            progress.update(task, completed=n, count=n)

        posts = scraper.fetch_posts(
            profile_id,
            max_posts=max_posts,
            visibility_filter=visibility if visibility != "ALL" else None,
            progress_callback=on_progress
        )

    if not posts:
        console.print("[yellow]⚠  No posts found. Check profile URL, privacy settings, or cookies.[/]")
        return

    console.print(f"\n[bold green]✔ Fetched {len(posts)} posts[/]\n")

    # ── Summary table ──
    t = Table(title="Quick Summary", border_style="dim", header_style="bold cyan")
    t.add_column("Metric", style="white")
    t.add_column("Count", style="bold yellow", justify="right")
    t.add_row("Total posts",  str(len(posts)))
    t.add_row("Public",       str(sum(1 for p in posts if p.get("privacy","").upper()=="PUBLIC")))
    t.add_row("Friends only", str(sum(1 for p in posts if p.get("privacy","").upper()=="FRIENDS")))
    t.add_row("Only Me",      str(sum(1 for p in posts if p.get("privacy","").upper()=="ONLY_ME")))
    t.add_row("Videos",       str(sum(1 for p in posts if p.get("is_video"))))
    t.add_row("Shared posts", str(sum(1 for p in posts if p.get("is_shared"))))
    console.print(t)
    console.print()

    # ── Exporting ──
    console.print(Rule("[bold yellow]Exporting[/]"))
    saved = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}[/]"),
        console=console
    ) as prog:

        if "links" in formats:
            t2 = prog.add_task("Exporting links (.txt)…")
            p = export_links(posts, out_dir)
            prog.update(t2, completed=True)
            if p: saved.append(("Links (.txt)", p))

        if "html" in formats:
            t2 = prog.add_task("Exporting HTML…")
            p = export_html(posts, out_dir, profile_id)
            prog.update(t2, completed=True)
            if p: saved.append(("HTML", p))

        if "pdf" in formats:
            t2 = prog.add_task("Exporting PDF…")
            p = export_pdf(posts, out_dir, profile_id)
            prog.update(t2, completed=True)
            if p: saved.append(("PDF", p))

        if "json" in formats:
            t2 = prog.add_task("Exporting JSON…")
            p = export_json(posts, out_dir)
            prog.update(t2, completed=True)
            if p: saved.append(("JSON", p))

        if "csv" in formats:
            t2 = prog.add_task("Exporting CSV…")
            p = export_csv(posts, out_dir)
            prog.update(t2, completed=True)
            if p: saved.append(("CSV", p))

        if "md" in formats:
            t2 = prog.add_task("Exporting Markdown…")
            p = export_markdown(posts, out_dir, profile_id)
            prog.update(t2, completed=True)
            if p: saved.append(("Markdown", p))

    # ── Done ──
    console.print()
    console.print(Panel(
        "\n".join(f"  [green]✔[/] [bold]{fmt}[/]  [dim]{path}[/]"
                  for fmt, path in saved),
        title="[bold green]✅ Export Complete[/]",
        border_style="green"
    ))
    console.print(
        f"\n[bold cyan]All files saved to:[/] [white]{out_dir}[/]\n"
    )


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/]")
        traceback.print_exc()
