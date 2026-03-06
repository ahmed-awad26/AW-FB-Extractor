# AW FB Extractor

```
 █████╗ ██╗    ██╗    ███████╗██████╗
██╔══██╗██║    ██║    ██╔════╝██╔══██╗
███████║██║ █╗ ██║    █████╗  ██████╔╝
██╔══██║██║███╗██║    ██╔══╝  ██╔══██╗
██║  ██║╚███╔███╔╝    ██║     ██████╔╝
╚═╝  ╚═╝ ╚══╝╚══╝     ╚═╝     ╚═════╝
Facebook Post Extractor  v1.0  |  by AW
```

A powerful Termux-based tool to extract, archive, and export Facebook posts from any profile in multiple formats.

---

## Features

| Feature | Details |
|---|---|
| **Post extraction** | Scrapes all posts from any public profile |
| **Visibility filter** | Public / Friends Only / Only Me |
| **Shared posts** | Fetches original shared content + source link |
| **Video posts** | Detects videos, saves thumbnail + direct link |
| **Export: Links** | Plain `.txt` list of all post URLs |
| **Export: HTML** | Full interactive web archive with search & filters |
| **Export: PDF** | Formatted, printable report with stats |
| **Export: JSON** | Complete machine-readable data |
| **Export: CSV** | Spreadsheet-compatible format |
| **Export: Markdown** | Clean `.md` file |
| **Cookie auth** | Login via browser cookies for private posts |

---

## Installation (Termux)

### One-command install:
```bash
curl -sL https://raw.githubusercontent.com/ahmed-awad26/AW-FB-Extractor/main/install.sh | bash
```

### Manual install:
```bash
pkg update -y
pkg install python python-pip git -y
git clone https://github.com/ahmed-awad26/AW-FB-Extractor
cd AW-FB-Extractor
pip install -r requirements.txt
python fb_extractor.py
```

---

## Usage

```bash
# Run directly:
python fb_extractor.py

# Or with the shortcut (after install.sh):
fbx
```

### Interactive Steps:
1. **Profile URL** — paste the Facebook URL or just the username
2. **Cookies** — optional; needed for Friends/Only Me posts
3. **Visibility filter** — All / Public / Friends / Only Me
4. **Export options** — choose formats (1–7 or "all")

---

## Cookie Setup (for private posts)

To access **Friends Only** or **Only Me** posts, you need to provide your login cookies:

1. Install [Cookie-Editor](https://cookie-editor.com/) extension in Chrome
2. Log in to `facebook.com`
3. Open Cookie-Editor → click **Export** → save as `fb_cookies.json`
4. When prompted in the tool, enter the path to that file

---

## Supported Export Formats

### HTML Archive
A fully interactive single-page web app with:
- Live search across all post content
- Filter by: All / Public / Friends / Only Me / Videos / Shared
- Video thumbnails with direct watch links
- Shared post attribution with original content
- Stats dashboard

### PDF Report
- Cover page with statistics breakdown
- Each post formatted with date, privacy badge, reactions
- Clickable URLs and video links
- Shared post sections with source attribution

### JSON
Full structured data for programmatic use.

### CSV
Compatible with Excel, Google Sheets, LibreOffice.

### Markdown
Clean readable format, good for documentation.

### Links (.txt)
Raw list of post URLs for quick reference.

---

## Notes

- Only **public posts** are accessible without cookies
- Facebook may limit scraping rate — add delays for large profiles
- This tool is for personal/archival use only
- Respect Facebook's Terms of Service

---

## Requirements

```
facebook-scraper>=0.2.59
rich>=13.0.0
fpdf2>=2.7.0
requests>=2.28.0
Pillow>=9.0.0
```

---

## Author

**AW** — [github.com/ahmed-awad26](https://github.com/ahmed-awad26)

---

> Built for Termux. All terminal output in English for compatibility.
