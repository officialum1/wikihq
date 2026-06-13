import bz2
import html
import logging
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Iterable, Dict, Any

import mwparserfromhell
import mwxml
import psycopg2
import requests
from elasticsearch import Elasticsearch
from elasticsearch import ElasticsearchException, helpers
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import execute_values


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://wiki:wiki@localhost:5432/wikipedia")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
WIKIPEDIA_DUMP_URL = os.getenv(
    "WIKIPEDIA_DUMP_URL",
    "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2",
)
DUMP_PATH = Path(os.getenv("DUMP_PATH", "/data/enwiki-latest-pages-articles.xml.bz2"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
RUN_ONCE = os.getenv("RUN_ONCE", "false").lower() == "true"
REFRESH_INTERVAL_SECONDS = int(os.getenv("REFRESH_INTERVAL_SECONDS", "86400"))
INDEX_NAME = "articles"

HEADING_RE = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$")
LIST_RE = re.compile(r"^([*#]+)\s*(.*)$")
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("wikipedia-worker")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "article"


def normalize_title(raw_title: str) -> str:
    title = " ".join(raw_title.replace("_", " ").split())
    return title[:1].upper() + title[1:] if title else title


def inline_wikitext_to_html(value: str) -> str:
    value = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", value)
    value = re.sub(r"\[(https?://[^\s\]]+)\s+([^\]]+)\]", r"\2", value)
    value = value.replace("'''", "").replace("''", "")
    parsed = mwparserfromhell.parse(value)
    clean = str(parsed.strip_code(normalize=True, collapse=True)).strip()
    return html.escape(clean)


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


def count_words(wikitext: str) -> int:
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


def connect() -> PgConnection:
    return psycopg2.connect(DATABASE_URL)


def ensure_tables(conn: PgConnection) -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            page_id BIGINT UNIQUE,
            title VARCHAR(512) UNIQUE NOT NULL,
            content TEXT NOT NULL,
            html_content TEXT NOT NULL,
            word_count INTEGER NOT NULL DEFAULT 0,
            is_user_created BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_articles_page_id ON articles(page_id)",
        "CREATE INDEX IF NOT EXISTS ix_articles_title ON articles(title)",
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'editor',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS article_revisions (
            id SERIAL PRIMARY KEY,
            article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            content TEXT NOT NULL,
            edit_summary VARCHAR(500) NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_article_revisions_article_id ON article_revisions(article_id)",
        "CREATE INDEX IF NOT EXISTS ix_article_revisions_user_id ON article_revisions(user_id)",
        """
        CREATE TABLE IF NOT EXISTS import_progress (
            id INTEGER PRIMARY KEY,
            last_page_id BIGINT NOT NULL DEFAULT 0,
            total_imported INTEGER NOT NULL DEFAULT 0,
            status VARCHAR(50) NOT NULL DEFAULT 'idle',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            slug VARCHAR(255) UNIQUE NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_categories_name ON categories(name)",
        "CREATE INDEX IF NOT EXISTS ix_categories_slug ON categories(slug)",
        """
        CREATE TABLE IF NOT EXISTS article_categories (
            article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            PRIMARY KEY (article_id, category_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS article_links (
            id SERIAL PRIMARY KEY,
            source_article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            target_title VARCHAR(512) NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_article_links_source_article_id ON article_links(source_article_id)",
        "CREATE INDEX IF NOT EXISTS ix_article_links_target_title ON article_links(target_title)",
        """
        CREATE TABLE IF NOT EXISTS redirects (
            id SERIAL PRIMARY KEY,
            source_title VARCHAR(512) NOT NULL UNIQUE,
            target_title VARCHAR(512) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_redirects_source_title ON redirects(source_title)",
        "CREATE INDEX IF NOT EXISTS ix_redirects_target_title ON redirects(target_title)",
        """
        CREATE TABLE IF NOT EXISTS templates (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            content TEXT NOT NULL,
            description VARCHAR(500) NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_templates_name ON templates(name)",
    ]
    with conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)
        cur.execute(
            """
            INSERT INTO import_progress (id, last_page_id, total_imported, status, updated_at)
            VALUES (1, 0, 0, 'idle', NOW())
            ON CONFLICT (id) DO NOTHING
            """
        )
    conn.commit()


def set_progress_status(conn: PgConnection, status: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE import_progress SET status = %s, updated_at = NOW() WHERE id = 1",
            (status,),
        )
    conn.commit()


def read_progress(conn: PgConnection) -> tuple[int, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT last_page_id, total_imported FROM import_progress WHERE id = 1")
        row = cur.fetchone()
    if row is None:
        return 0, 0
    return int(row[0]), int(row[1])


def update_progress(conn: PgConnection, last_page_id: int, imported_count: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE import_progress
            SET last_page_id = %s,
                total_imported = total_imported + %s,
                status = 'running',
                updated_at = NOW()
            WHERE id = 1
            """,
            (last_page_id, imported_count),
        )
    conn.commit()


def download_dump() -> None:
    if DUMP_PATH.exists() and DUMP_PATH.stat().st_size > 0:
        logger.info("Using existing dump at %s", DUMP_PATH)
        return

    DUMP_PATH.parent.mkdir(parents=True, exist_ok=True)
    partial_path = DUMP_PATH.with_suffix(DUMP_PATH.suffix + ".part")
    resume_at = partial_path.stat().st_size if partial_path.exists() else 0
    headers = {"Range": f"bytes={resume_at}-"} if resume_at else {}
    mode = "ab" if resume_at else "wb"

    logger.info("Downloading Wikipedia dump from %s", WIKIPEDIA_DUMP_URL)
    with requests.get(WIKIPEDIA_DUMP_URL, headers=headers, stream=True, timeout=60) as response:
        if response.status_code == 200 and resume_at:
            partial_path.unlink(missing_ok=True)
            resume_at = 0
            mode = "wb"
        response.raise_for_status()
        with partial_path.open(mode) as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
    partial_path.replace(DUMP_PATH)
    logger.info("Downloaded dump to %s", DUMP_PATH)


def ensure_search_index(client: Elasticsearch) -> None:
    if client.indices.exists(index=INDEX_NAME):
        return
    client.indices.create(
        index=INDEX_NAME,
        mappings={
            "properties": {
                "id": {"type": "integer"},
                "page_id": {"type": "long"},
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "content": {"type": "text"},
                "html_content": {"type": "text"},
                "word_count": {"type": "integer"},
                "updated_at": {"type": "date"},
            }
        },
    )


def iter_pages(last_page_id: int) -> Iterable[Dict[str, Any]]:
    with bz2.open(DUMP_PATH, "rb") as dump_file:
        dump = mwxml.Dump.from_file(dump_file)
        for page in dump:
            page_id = int(page.id)
            namespace = int(getattr(page, "namespace", 0))
            # We process articles (0), templates (10). File descriptions (6) if needed.
            if namespace not in (0, 10) or page_id <= last_page_id:
                continue

            redirect = normalize_title(page.redirect) if getattr(page, "redirect", None) else None

            latest_revision = None
            for revision in page:
                latest_revision = revision

            if latest_revision is None or not latest_revision.text:
                continue

            yield {
                "page_id": page_id,
                "title": normalize_title(page.title),
                "content": latest_revision.text,
                "namespace": namespace,
                "redirect": redirect
            }


def fetch_article_ids(conn: PgConnection, page_ids: list[int]) -> dict[int, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT page_id, id FROM articles WHERE page_id = ANY(%s)", (page_ids,))
        rows = cur.fetchall()
    return {int(page_id): int(article_id) for page_id, article_id in rows}


def flush_batch(
    conn: PgConnection,
    search_client: Elasticsearch | None,
    articles: list[Dict[str, Any]],
    redirects: list[Dict[str, Any]],
    templates: list[Dict[str, Any]]
) -> int:
    if not articles and not redirects and not templates:
        return 0

    with conn.cursor() as cur:
        # 1. Insert Templates
        if templates:
            template_rows = [(t["title"].replace("Template:", ""), t["content"]) for t in templates]
            execute_values(
                cur,
                """
                INSERT INTO templates (name, content, created_at, updated_at)
                VALUES %s
                ON CONFLICT (name) DO UPDATE
                SET content = EXCLUDED.content,
                    updated_at = NOW()
                """,
                template_rows,
                template="(%s, %s, NOW(), NOW())"
            )

        # 2. Insert Redirects
        if redirects:
            redirect_rows = [(r["title"], r["redirect"]) for r in redirects]
            execute_values(
                cur,
                """
                INSERT INTO redirects (source_title, target_title, created_at)
                VALUES %s
                ON CONFLICT (source_title) DO UPDATE
                SET target_title = EXCLUDED.target_title
                """,
                redirect_rows,
                template="(%s, %s, NOW())"
            )

        # 3. Insert Articles
        if articles:
            article_rows = [
                (
                    a["page_id"],
                    a["title"],
                    a["content"],
                    wikitext_to_html(a["content"]),
                    count_words(a["content"])
                ) for a in articles
            ]
            execute_values(
                cur,
                """
                INSERT INTO articles (
                    page_id, title, content, html_content, word_count, is_user_created, created_at, updated_at
                )
                VALUES %s
                ON CONFLICT (page_id) DO UPDATE
                SET title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    html_content = EXCLUDED.html_content,
                    word_count = EXCLUDED.word_count,
                    is_user_created = FALSE,
                    updated_at = NOW()
                """,
                article_rows,
                template="(%s, %s, %s, %s, %s, FALSE, NOW(), NOW())",
                page_size=len(article_rows),
            )
            
            # Categories and Links for articles
            conn.commit()
            page_to_article = fetch_article_ids(conn, [a["page_id"] for a in articles])
            article_ids = list(page_to_article.values())
            
            # Sync Categories
            category_names = sorted({c for a in articles for c in extract_categories(a["content"])})
            if category_names:
                category_rows = [(name, slugify(name)) for name in category_names]
                execute_values(
                    cur,
                    "INSERT INTO categories (name, slug) VALUES %s ON CONFLICT (slug) DO NOTHING",
                    category_rows,
                )
                cur.execute(
                    "SELECT id, slug FROM categories WHERE slug = ANY(%s)",
                    ([slug for _, slug in category_rows],),
                )
                slug_to_id = {slug: category_id for category_id, slug in cur.fetchall()}
                cur.execute("DELETE FROM article_categories WHERE article_id = ANY(%s)", (article_ids,))

                relationships = []
                for a in articles:
                    article_id = page_to_article.get(a["page_id"])
                    if not article_id:
                        continue
                    for category in extract_categories(a["content"]):
                        category_id = slug_to_id.get(slugify(category))
                        if category_id:
                            relationships.append((article_id, category_id))
                if relationships:
                    execute_values(
                        cur,
                        "INSERT INTO article_categories (article_id, category_id) VALUES %s ON CONFLICT DO NOTHING",
                        relationships,
                    )
            else:
                cur.execute("DELETE FROM article_categories WHERE article_id = ANY(%s)", (article_ids,))
            
            # Sync Links
            cur.execute("DELETE FROM article_links WHERE source_article_id = ANY(%s)", (article_ids,))
            link_relationships = []
            for a in articles:
                article_id = page_to_article.get(a["page_id"])
                if not article_id:
                    continue
                for target in extract_links(a["content"]):
                    link_relationships.append((article_id, target))
            if link_relationships:
                execute_values(
                    cur,
                    "INSERT INTO article_links (source_article_id, target_title) VALUES %s",
                    link_relationships,
                )
            
            # Index to ElasticSearch
            if search_client is not None:
                actions = []
                for a in articles:
                    article_id = page_to_article.get(a["page_id"])
                    if not article_id:
                        continue
                    actions.append(
                        {
                            "_index": INDEX_NAME,
                            "_id": article_id,
                            "_source": {
                                "id": article_id,
                                "page_id": a["page_id"],
                                "title": a["title"],
                                "content": a["content"],
                                "html_content": wikitext_to_html(a["content"]),
                                "word_count": count_words(a["content"]),
                                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            },
                        }
                    )
                if actions:
                    try:
                        helpers.bulk(search_client, actions, request_timeout=120)
                    except ElasticsearchException as exc:
                        logger.warning("Elasticsearch indexing failed for batch: %s", exc)
                        
    conn.commit()

    all_pages = articles + templates + redirects
    last_page_id = max(p["page_id"] for p in all_pages) if all_pages else 0
    if last_page_id:
        update_progress(conn, last_page_id, len(articles))
    return len(articles)


def import_dump() -> None:
    conn = connect()
    search_client: Elasticsearch | None = None
    try:
        ensure_tables(conn)
        set_progress_status(conn, "running")
        download_dump()
        last_page_id, total_imported = read_progress(conn)
        logger.info("Resuming import after page_id=%s total_imported=%s", last_page_id, total_imported)

        try:
            search_client = Elasticsearch(ELASTICSEARCH_URL, request_timeout=30)
            ensure_search_index(search_client)
        except ElasticsearchException as exc:
            logger.warning("Elasticsearch unavailable; continuing without indexing: %s", exc)
            search_client = None

        articles_batch = []
        templates_batch = []
        redirects_batch = []
        imported_this_run = 0
        
        for page in iter_pages(last_page_id):
            if page["redirect"]:
                redirects_batch.append(page)
            elif page["namespace"] == 10:
                templates_batch.append(page)
            elif page["namespace"] == 0:
                articles_batch.append(page)

            if len(articles_batch) + len(templates_batch) + len(redirects_batch) >= BATCH_SIZE:
                imported = flush_batch(conn, search_client, articles_batch, redirects_batch, templates_batch)
                imported_this_run += imported
                logger.info("Processed batch; last_page_id=%s", page["page_id"])
                articles_batch.clear()
                templates_batch.clear()
                redirects_batch.clear()

        imported_this_run += flush_batch(conn, search_client, articles_batch, redirects_batch, templates_batch)
        set_progress_status(conn, "complete")
        logger.info("Import pass complete; imported_or_updated=%s", imported_this_run)
    except Exception:
        logger.exception("Import failed")
        try:
            set_progress_status(conn, "failed")
        finally:
            raise
    finally:
        conn.close()


def main() -> None:
    while True:
        try:
            import_dump()
        except Exception:
            logger.info("Worker will retry after %s seconds", REFRESH_INTERVAL_SECONDS)

        if RUN_ONCE:
            break

        logger.info("Sleeping for %s seconds before next import pass", REFRESH_INTERVAL_SECONDS)
        time.sleep(REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
