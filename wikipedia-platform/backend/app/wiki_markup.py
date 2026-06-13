import html
import re
import unicodedata

import mwparserfromhell


HEADING_RE = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$")
LIST_RE = re.compile(r"^([*#]+)\s*(.*)$")
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def normalize_title(raw_title: str) -> str:
    title = " ".join(raw_title.replace("_", " ").split())
    return title[:1].upper() + title[1:] if title else title


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "article"


def word_count(wikitext: str) -> int:
    plain_text = str(mwparserfromhell.parse(wikitext).strip_code(normalize=True, collapse=True))
    return len(WORD_RE.findall(plain_text))


def extract_categories(wikitext: str) -> list[str]:
    categories: list[str] = []
    code = mwparserfromhell.parse(wikitext)
    for link in code.filter_wikilinks():
        target = str(link.title).strip()
        if target.lower().startswith("category:"):
            category = target.split(":", 1)[1].strip()
            if category and category not in categories:
                categories.append(category)
    return categories


def extract_links(wikitext: str) -> list[str]:
    links: list[str] = []
    code = mwparserfromhell.parse(wikitext)
    for link in code.filter_wikilinks():
        target = str(link.title).strip()
        if target and not target.lower().startswith(("category:", "file:", "image:", "template:")):
            normalized = normalize_title(target)
            if normalized not in links:
                links.append(normalized)
    return links


def extract_interlanguage_links(wikitext: str) -> dict[str, str]:
    # e.g., [[es:Wikipedia:Portada]]
    links = {}
    code = mwparserfromhell.parse(wikitext)
    for link in code.filter_wikilinks():
        target = str(link.title).strip()
        parts = target.split(":", 1)
        # simplistic check for 2-3 letter language codes
        if len(parts) == 2 and 2 <= len(parts[0]) <= 3 and parts[0].islower():
            links[parts[0]] = parts[1].strip()
    return links

def inline_wikitext_to_html(value: str) -> str:
    value = html.escape(value)
    
    # Render files
    def render_file(match):
        target = match.group(1)
        options = match.group(2)
        if options:
            label = options.split('|')[-1]
        else:
            label = target
        return f'<img src="/api/files/download/{target}" alt="{label}" />'
    
    value = re.sub(r"\[\[(?:File|Image):([^|\]]+)(?:\|([^\]]+))?\]\]", render_file, value, flags=re.IGNORECASE)
    
    # Render wiki links
    def render_link(match):
        target = match.group(1)
        label = match.group(2) if match.group(2) else target
        return f'<a href="/wiki/{normalize_title(target)}">{label}</a>'
        
    value = re.sub(r"\[\[(?:([^|\]]+)\|)?([^\]]+)\]\]", render_link, value)
    
    # Render external links
    value = re.sub(r"\[(https?://[^\s\]]+)\s+([^\]]+)\]", r'<a href="\1" target="_blank" rel="noopener">\2</a>', value)
    
    # Bold / Italic
    value = value.replace("'''", "<strong>").replace("''", "<em>") # This is very simplistic but works for matched pairs
    return value


def wikitext_to_html(wikitext: str) -> str:
    parsed = mwparserfromhell.parse(wikitext)
    raw = str(parsed)
    blocks: list[str] = []
    open_list: str | None = None

    def close_list() -> None:
        nonlocal open_list
        if open_list:
            blocks.append(f"</{open_list}>")
            open_list = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            close_list()
            continue
        if stripped.lower().startswith("[[category:"):
            continue

        heading = HEADING_RE.match(stripped)
        if heading:
            close_list()
            level = min(len(heading.group(1)), 6)
            text = inline_wikitext_to_html(heading.group(2))
            heading_id = slugify(html.unescape(text))
            blocks.append(f'<h{level} id="{heading_id}">{text}</h{level}>')
            continue

        list_match = LIST_RE.match(stripped)
        if list_match:
            marker = list_match.group(1)[0]
            list_tag = "ul" if marker == "*" else "ol"
            if open_list != list_tag:
                close_list()
                open_list = list_tag
                blocks.append(f"<{list_tag}>")
            blocks.append(f"<li>{inline_wikitext_to_html(list_match.group(2))}</li>")
            continue

        close_list()
        blocks.append(f"<p>{inline_wikitext_to_html(stripped)}</p>")

    close_list()
    return "\n".join(blocks)

