# AW FB Extractor

```text
 █████╗ ██╗    ██╗    ███████╗██████╗
██╔══██╗██║    ██║    ██╔════╝██╔══██╗
███████║██║ █╗ ██║    █████╗  ██████╔╝
██╔══██║██║███╗██║    ██╔══╝  ██╔══██╗
██║  ██║╚███╔███╔╝    ██║     ██████╔╝
╚═╝  ╚═╝ ╚══╝╚══╝     ╚═╝     ╚═════╝
Facebook Post Extractor  v1.1  |  by AW
```

A polished Termux-first Facebook post archiver for exporting timeline data into clean, portable reports.

## Highlights

- Rich TUI workflow built for Termux
- Accepts full profile URLs, usernames, and numeric profile IDs
- Optional cookie-based access for non-public content
- Visibility filtering: All / Public / Friends / Only Me
- Multi-export pipeline: HTML, PDF, JSON, CSV, Markdown, Links TXT
- Profile probe before scraping to confirm the target is reachable
- Automatic diagnostic report when Facebook returns zero posts
- Self-healing installer for common Termux dependency issues

## Why v1.1 is better

This release keeps the existing panel style and author credits intact while improving the real-world setup flow:

- fixes `lxml_html_clean` dependency problems
- installs extra Termux build dependencies automatically
- adds a launcher command: `fbx`
- adds better empty-result diagnostics instead of just `No posts found`
- probes the profile first so you can tell whether the target is reachable

## Installation

### One-command install

```bash
curl -fsSL https://raw.githubusercontent.com/ahmed-awad26/AW-FB-Extractor/main/install.sh | bash
```

### Manual install

```bash
pkg update -y && pkg upgrade -y
pkg install -y python python-pip git clang libxml2 libxslt libffi openssl pkg-config rust
git clone https://github.com/ahmed-awad26/AW-FB-Extractor
cd AW-FB-Extractor
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python fb_extractor.py
```

## Usage

```bash
# main launcher
fbx

# direct run
cd ~/AW-FB-Extractor
python fb_extractor.py
```

## Workflow

1. Enter a Facebook profile URL, username, or numeric ID.
2. Choose whether to load cookies.
3. Pick the visibility filter.
4. Choose the max posts and export format(s).
5. Save the results to your preferred output directory.

## Export formats

| Format | Use case |
|---|---|
| HTML | interactive archive with search + filters |
| PDF | printable report |
| JSON | automation / structured data |
| CSV | Excel / Sheets analysis |
| Markdown | documentation-ready output |
| TXT links | quick post URL list |

## Cookies

Cookies are optional, but they help when:

- a profile is partially visible only when logged in
- you need Friends-only data you are allowed to view
- Facebook serves an empty feed to anonymous requests

Export cookies from a browser that is already logged into Facebook, then point the tool to the JSON file.

## Zero-post troubleshooting

If the tool says no posts were found even though the profile has public posts, the most common reasons are:

- Facebook returned an empty or blocked feed to the scraper session
- the target profile is reachable, but the timeline endpoint returned no items
- cookies are expired or missing for content that is not fully public
- `facebook-scraper` itself is inconsistent on some profiles/pages

The tool now saves a `debug_*.txt` diagnostic report automatically when that happens.

## Notes

- Without cookies, only content that Facebook exposes publicly to the scraper session can be collected.
- Some public profiles still return zero posts because Facebook changes its frontend behavior frequently.
- Testing with a well-known public page can help confirm whether the issue is target-specific or environment-specific.

## Requirements

- Termux from F-Droid
- Python 3 on Termux
- Internet access
- Optional: fresh Facebook cookies in JSON format

## Author

**AW** — github.com/ahmed-awad26

Built for Termux. Terminal text stays in English for compatibility.
