import json
from datetime import datetime, timezone


from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from . import search
from .auth import create_access_token, get_current_user, hash_password, verify_password
from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Article, ArticleRevision, Category, ImportProgress, User
from .models import ArticleLink, FileAsset, Namespace, PageProtection, PatrolLog, Redirect, TalkMessage, Template, WatchlistItem
from .schemas import (
    ArticleCreate,
    ArticleOut,
    ArticleUpdate,
    BacklinkOut,
    CategoryMemberOut,
    FileAssetCreate,
    FileAssetOut,
    NamespaceOut,
    PageProtectionCreate,
    PageProtectionOut,
    PatrolItemOut,
    ProgressOut,
    PageInfoOut,
    RecentChangeOut,
    RedirectCreate,
    RedirectOut,
    RevisionOut,
    SearchResponse,
    SearchResult,
    SpecialPageOut,
    StatisticsOut,
    TalkMessageCreate,
    TalkMessageOut,
    TemplateCreate,
    TemplateOut,
    Token,
    UserLogin,
    UserOut,
    UserRegister,
    WatchlistItemOut,
)
from .wiki_markup import extract_categories, extract_links, extract_interlanguage_links, normalize_title, slugify, wikitext_to_html, word_count


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


def article_to_schema(article: Article) -> ArticleOut:
    return ArticleOut(
        id=article.id,
        page_id=article.page_id,
        title=article.title,
        content=article.content,
        html_content=article.html_content,
        word_count=article.word_count,
        is_user_created=article.is_user_created,
        categories=[category.name for category in article.categories],
        interlanguage_links=extract_interlanguage_links(article.content),
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


def ensure_progress_row(db: Session) -> ImportProgress:
    progress = db.get(ImportProgress, 1)
    if progress is None:
        progress = ImportProgress(id=1, last_page_id=0, total_imported=0, status="idle")
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def get_or_create_categories(db: Session, names: list[str]) -> list[Category]:
    categories: list[Category] = []
    seen: set[str] = set()
    for raw_name in names:
        name = " ".join(raw_name.split())
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        slug = slugify(name)
        category = db.query(Category).filter(Category.slug == slug).first()
        if category is None:
            category = Category(name=name, slug=slug)
            db.add(category)
            db.flush()
        categories.append(category)
    return categories


def sync_links(db: Session, article_id: int, links: list[str]) -> None:
    db.query(ArticleLink).filter(ArticleLink.source_article_id == article_id).delete()
    if not links:
        return
    link_rows = [
        ArticleLink(source_article_id=article_id, target_title=target)
        for target in set(links)
    ]
    db.add_all(link_rows)
    db.flush()


import mwparserfromhell

def expand_templates(db: Session, wikitext: str, depth=0) -> str:
    if depth > 5:
        return wikitext
    code = mwparserfromhell.parse(wikitext)
    templates_found = code.filter_templates()
    if not templates_found:
        return wikitext
    
    for template_node in templates_found:
        name = str(template_node.name).strip()
        template_obj = db.query(Template).filter(Template.name == name).first()
        if template_obj:
            content = template_obj.content
            for i, param in enumerate(template_node.params):
                p_name = str(param.name).strip() if param.showkey else str(i + 1)
                p_val = str(param.value)
                content = content.replace(f"{{{{{{{p_name}}}}}}}", p_val)
            expanded = expand_templates(db, content, depth + 1)
            try:
                code.replace(template_node, expanded)
            except ValueError:
                pass
    return str(code)



def cache_key_for_title(title: str) -> str:
    return f"article:{normalize_title(title).lower()}"


def cache_article(article: Article) -> None:
    try:
        payload = article_to_schema(article).model_dump(mode="json")
        redis_client.setex(cache_key_for_title(article.title), 300, json.dumps(payload))
    except RedisError:
        return


def clear_article_cache(title: str) -> None:
    try:
        redis_client.delete(cache_key_for_title(title))
    except RedisError:
        return


def parse_search_datetime(value: object) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


def seed_namespaces(db: Session) -> None:
    defaults = [
        ("Main", "main", "Default article namespace."),
        ("Talk", "talk", "Discussion pages attached to articles."),
        ("User", "user", "User profile and sandbox pages."),
        ("File", "file", "Uploaded media and file description pages."),
        ("Template", "template", "Reusable transclusion snippets."),
        ("Category", "category", "Category landing pages."),
        ("Special", "special", "System-generated utility pages."),
        ("Help", "help", "Documentation pages for the wiki."),
    ]
    for name, slug, description in defaults:
        if db.query(Namespace).filter(Namespace.slug == slug).first() is None:
            db.add(Namespace(name=name, slug=slug, description=description))
    db.commit()


def seed_admin_user(db: Session) -> None:
    if not settings.admin_bootstrap_password:
        return
    username = settings.admin_bootstrap_username or "admin"
    email = (settings.admin_bootstrap_email or "admin@wikihq.local").lower()
    user = db.query(User).filter(or_(User.username == username, User.email == email)).first()
    if user is None:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(settings.admin_bootstrap_password),
            role="admin",
        )
        db.add(user)
    else:
        user.role = "admin"
    db.commit()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_progress_row(db)
        seed_namespaces(db)
        seed_admin_user(db)
    try:
        search.ensure_index()
    except Exception:
        pass


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> Token:
    username = payload.username.strip()
    email = payload.email.lower()
    existing = db.query(User).filter(or_(User.username == username, User.email == email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already exists")
    user = User(username=username, email=email, password_hash=hash_password(payload.password), role="editor")
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token(user), username=user.username, role=user.role)


@app.post("/api/auth/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    username_or_email = payload.username_or_email.strip()
    user = (
        db.query(User)
        .filter(or_(User.username == username_or_email, User.email == username_or_email.lower()))
        .first()
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return Token(access_token=create_access_token(user), username=user.username, role=user.role)


@app.post("/api/auth/admin/login", response_model=Token)
def admin_login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    username_or_email = payload.username_or_email.strip()
    user = (
        db.query(User)
        .filter(or_(User.username == username_or_email, User.email == username_or_email.lower()))
        .first()
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if user.role not in {"admin", "sysop"}:
        raise HTTPException(status_code=403, detail="Admin role required")
    return Token(access_token=create_access_token(user), username=user.username, role=user.role)


@app.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@app.get("/api/progress", response_model=ProgressOut)
def progress(db: Session = Depends(get_db)) -> ImportProgress:
    return ensure_progress_row(db)


@app.get("/api/special/pages", response_model=list[SpecialPageOut])
def special_pages() -> list[SpecialPageOut]:
    return [
        SpecialPageOut(
            title="Recent changes",
            path="/special/recent-changes",
            description="Latest article edits and imports.",
            section="Maintenance",
        ),
        SpecialPageOut(
            title="Random article",
            path="/special/random",
            description="Open a random article from the wiki.",
            section="Navigation",
        ),
        SpecialPageOut(
            title="Import progress",
            path="/admin/progress",
            description="Wikipedia dump worker status.",
            section="Maintenance",
        ),
        SpecialPageOut(
            title="Maintenance Jobs",
            path="/admin/maintenance",
            description="Run background maintenance tasks.",
            section="Maintenance",
        ),
        SpecialPageOut(
            title="Search",
            path="/search",
            description="Search article titles and body text.",
            section="Navigation",
        ),
        SpecialPageOut(
            title="Watchlist",
            path="/special/watchlist",
            description="Pages followed by the current user.",
            section="Personal",
        ),
        SpecialPageOut(
            title="Namespaces",
            path="/special/namespaces",
            description="Configured content namespaces.",
            section="Administration",
        ),
        SpecialPageOut(
            title="Redirects",
            path="/special/redirects",
            description="Redirect source and target pages.",
            section="Maintenance",
        ),
        SpecialPageOut(
            title="Files",
            path="/special/files",
            description="Uploaded media description records.",
            section="Content",
        ),
        SpecialPageOut(
            title="Templates",
            path="/special/templates",
            description="Reusable wiki template snippets.",
            section="Content",
        ),
        SpecialPageOut(
            title="Patrol",
            path="/special/patrol",
            description="Review queue for recent edits.",
            section="Moderation",
        ),
        SpecialPageOut(
            title="Statistics",
            path="/special/statistics",
            description="Wiki content and user counts.",
            section="Maintenance",
        ),
    ]


@app.get("/api/namespaces", response_model=list[NamespaceOut])
def namespaces(db: Session = Depends(get_db)) -> list[Namespace]:
    seed_namespaces(db)
    return db.query(Namespace).order_by(Namespace.id.asc()).all()


@app.get("/api/recent-changes", response_model=list[RecentChangeOut])
def recent_changes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[RecentChangeOut]:
    offset = (page - 1) * page_size
    revisions = (
        db.query(ArticleRevision)
        .join(Article, Article.id == ArticleRevision.article_id)
        .outerjoin(User, User.id == ArticleRevision.user_id)
        .options(selectinload(ArticleRevision.article), selectinload(ArticleRevision.user))
        .order_by(ArticleRevision.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [
        RecentChangeOut(
            id=revision.id,
            article_id=revision.article_id,
            title=revision.article.title,
            username=revision.user.username if revision.user else None,
            edit_summary=revision.edit_summary,
            created_at=revision.created_at,
        )
        for revision in revisions
    ]


@app.get("/api/random", response_model=ArticleOut)
def random_article(db: Session = Depends(get_db)) -> ArticleOut:
    article = (
        db.query(Article)
        .options(selectinload(Article.categories))
        .order_by(func.random())
        .first()
    )
    if article is None:
        raise HTTPException(status_code=404, detail="No articles available")
    return article_to_schema(article)


@app.get("/api/watchlist", response_model=list[WatchlistItemOut])
def watchlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[WatchlistItemOut]:
    items = (
        db.query(WatchlistItem)
        .options(selectinload(WatchlistItem.article))
        .filter(WatchlistItem.user_id == current_user.id)
        .order_by(WatchlistItem.created_at.desc())
        .all()
    )
    return [
        WatchlistItemOut(
            id=item.id,
            article_id=item.article_id,
            title=item.article.title,
            created_at=item.created_at,
        )
        for item in items
    ]


@app.post("/api/watchlist/{article_id}", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
def watch_article(
    article_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistItemOut:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == current_user.id, WatchlistItem.article_id == article_id)
        .first()
    )
    if item is None:
        item = WatchlistItem(user_id=current_user.id, article_id=article_id)
        db.add(item)
        db.commit()
        db.refresh(item)
    return WatchlistItemOut(id=item.id, article_id=article.id, title=article.title, created_at=item.created_at)


@app.delete("/api/watchlist/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    article_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == current_user.id, WatchlistItem.article_id == article_id)
        .first()
    )
    if item:
        db.delete(item)
        db.commit()


@app.get("/api/files", response_model=list[FileAssetOut])
def files(db: Session = Depends(get_db)) -> list[FileAssetOut]:
    assets = (
        db.query(FileAsset)
        .options(selectinload(FileAsset.uploader))
        .order_by(FileAsset.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        FileAssetOut(
            id=asset.id,
            title=asset.title,
            filename=asset.filename,
            mime_type=asset.mime_type,
            size_bytes=asset.size_bytes,
            description=asset.description,
            uploader=asset.uploader.username if asset.uploader else None,
            created_at=asset.created_at,
        )
        for asset in assets
    ]


@app.post("/api/files", response_model=FileAssetOut, status_code=status.HTTP_201_CREATED)
def create_file_asset(
    payload: FileAssetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileAssetOut:
    asset = FileAsset(
        title=normalize_title(payload.title),
        filename=payload.filename,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        description=payload.description,
        uploader_id=current_user.id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return FileAssetOut(
        id=asset.id,
        title=asset.title,
        filename=asset.filename,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        description=asset.description,
        uploader=current_user.username,
        created_at=asset.created_at,
    )

@app.post("/api/files/upload", response_model=FileAssetOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileAssetOut:
    filename = file.filename or "unknown"
    safe_filename = f"{datetime.now().timestamp()}_{filename.replace(' ', '_')}"
    file_path = os.path.join("uploads", safe_filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        size_bytes = len(content)
        
    asset = FileAsset(
        title=normalize_title(title),
        filename=safe_filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        description=description,
        uploader_id=current_user.id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return FileAssetOut(
        id=asset.id,
        title=asset.title,
        filename=asset.filename,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        uploader=current_user.username,
        created_at=asset.created_at,
    )

from fastapi.responses import FileResponse

@app.get("/api/files/download/{title:path}")
def download_file(title: str, db: Session = Depends(get_db)):
    normalized = normalize_title(title)
    asset = db.query(FileAsset).filter(FileAsset.title == normalized).first()
    if not asset:
        raise HTTPException(status_code=404, detail="File not found")
    file_path = os.path.join("uploads", asset.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File content missing")
    return FileResponse(file_path, media_type=asset.mime_type, filename=asset.title)


@app.get("/api/templates", response_model=list[TemplateOut])
def templates(db: Session = Depends(get_db)) -> list[Template]:
    return db.query(Template).order_by(Template.updated_at.desc()).limit(100).all()


@app.post("/api/templates", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Template:
    existing = db.query(Template).filter(Template.name == payload.name).first()
    if existing:
        existing.content = payload.content
        existing.description = payload.description
        db.commit()
        db.refresh(existing)
        return existing
    template = Template(name=payload.name, content=payload.content, description=payload.description)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@app.get("/api/redirects", response_model=list[RedirectOut])
def redirects(db: Session = Depends(get_db)) -> list[Redirect]:
    return db.query(Redirect).order_by(Redirect.created_at.desc()).limit(100).all()


@app.post("/api/redirects", response_model=RedirectOut, status_code=status.HTTP_201_CREATED)
def create_redirect(
    payload: RedirectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Redirect:
    redirect = Redirect(
        source_title=normalize_title(payload.source_title),
        target_title=normalize_title(payload.target_title),
    )
    db.add(redirect)
    db.commit()
    db.refresh(redirect)
    return redirect


@app.get("/api/patrol", response_model=list[PatrolItemOut])
def patrol_queue(db: Session = Depends(get_db)) -> list[PatrolItemOut]:
    revisions = (
        db.query(ArticleRevision)
        .options(selectinload(ArticleRevision.article), selectinload(ArticleRevision.user))
        .order_by(ArticleRevision.created_at.desc())
        .limit(50)
        .all()
    )
    patrol_by_revision = {
        log.revision_id: log
        for log in db.query(PatrolLog)
        .filter(PatrolLog.revision_id.in_([revision.id for revision in revisions] or [0]))
        .all()
    }
    return [
        PatrolItemOut(
            revision_id=revision.id,
            article_id=revision.article_id,
            title=revision.article.title,
            username=revision.user.username if revision.user else None,
            status=patrol_by_revision.get(revision.id).status if revision.id in patrol_by_revision else "unreviewed",
            edit_summary=revision.edit_summary,
            created_at=revision.created_at,
        )
        for revision in revisions
    ]


@app.get("/api/statistics", response_model=StatisticsOut)
def statistics(db: Session = Depends(get_db)) -> StatisticsOut:
    return StatisticsOut(
        articles=db.query(Article).count(),
        users=db.query(User).count(),
        revisions=db.query(ArticleRevision).count(),
        categories=db.query(Category).count(),
        files=db.query(FileAsset).count(),
        templates=db.query(Template).count(),
    )


@app.get("/api/search", response_model=SearchResponse)
def search_endpoint(
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> SearchResponse:
    query = q.strip()
    try:
        elastic_results = search.search_articles(query, page, page_size)
        results: list[SearchResult] = []
        for hit in elastic_results["hits"]:
            source = hit["_source"]
            highlight = hit.get("highlight", {})
            snippet = " ".join(highlight.get("content") or highlight.get("html_content") or [])
            if not snippet:
                snippet = source.get("content", "")[:220]
            updated = source.get("updated_at")
            results.append(
                SearchResult(
                    id=source["id"],
                    title=source["title"],
                    snippet=snippet,
                    word_count=source.get("word_count", 0),
                    updated_at=parse_search_datetime(updated),
                )
            )
        return SearchResponse(query=query, page=page, page_size=page_size, total=elastic_results["total"], results=results)
    except Exception:
        offset = (page - 1) * page_size
        base_query = db.query(Article).filter(
            or_(Article.title.ilike(f"%{query}%"), Article.content.ilike(f"%{query}%"))
        )
        total = base_query.count()
        articles = base_query.order_by(Article.updated_at.desc()).offset(offset).limit(page_size).all()
        return SearchResponse(
            query=query,
            page=page,
            page_size=page_size,
            total=total,
            results=[
                SearchResult(
                    id=article.id,
                    title=article.title,
                    snippet=article.content[:220],
                    word_count=article.word_count,
                    updated_at=article.updated_at,
                )
                for article in articles
            ],
        )

@app.get("/api/search/suggest", response_model=list[str])
def suggest_endpoint(q: str = Query(min_length=1), db: Session = Depends(get_db)) -> list[str]:
    query = q.strip()
    try:
        # If elasticsearch is configured and running
        elastic_results = search.search_articles(query, 1, 10)
        return [hit["_source"]["title"] for hit in elastic_results["hits"]]
    except Exception:
        # Fallback to database
        articles = db.query(Article).filter(Article.title.ilike(f"{query}%")).limit(10).all()
        return [article.title for article in articles]




@app.post("/api/article", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleOut:
    title = normalize_title(payload.title)
    if db.query(Article).filter(Article.title == title).first():
        raise HTTPException(status_code=409, detail="Article already exists")
    category_names = [*extract_categories(payload.content), *payload.categories]
    expanded_content = expand_templates(db, payload.content)
    article = Article(
        title=title,
        content=payload.content,
        html_content=wikitext_to_html(expanded_content),
        word_count=word_count(payload.content),
        is_user_created=True,
        categories=get_or_create_categories(db, category_names),
    )
    db.add(article)
    db.flush()
    db.add(
        ArticleRevision(
            article_id=article.id,
            user_id=current_user.id,
            content=payload.content,
            edit_summary=payload.edit_summary,
        )
    )
    db.commit()
    db.refresh(article)
    sync_links(db, article.id, extract_links(payload.content))
    db.commit()
    try:
        search.index_article(article)
    except Exception:
        pass
    cache_article(article)
    return article_to_schema(article)


@app.put("/api/article/{article_id}", response_model=ArticleOut)
def update_article(
    article_id: int,
    payload: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleOut:
    article = db.query(Article).options(selectinload(Article.categories)).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
        
    protection = db.query(PageProtection).filter(PageProtection.article_id == article.id).first()
    if protection:
        if protection.level in ["sysop", "admin"] and current_user.role not in ["sysop", "admin"]:
            raise HTTPException(status_code=403, detail="This page is fully protected.")
        if protection.level == "autoconfirmed" and not current_user:
            raise HTTPException(status_code=403, detail="This page is semi-protected.")

    if payload.categories is not None:
        category_names = [*extract_categories(payload.content), *payload.categories]
        article.categories = get_or_create_categories(db, category_names)
    article.content = payload.content
    expanded_content = expand_templates(db, payload.content)
    article.html_content = wikitext_to_html(expanded_content)
    article.word_count = word_count(payload.content)
    article.is_user_created = article.is_user_created or article.page_id is None
    db.add(
        ArticleRevision(
            article_id=article.id,
            user_id=current_user.id,
            content=payload.content,
            edit_summary=payload.edit_summary,
        )
    )
    db.commit()
    db.refresh(article)
    sync_links(db, article.id, extract_links(payload.content))
    db.commit()
    clear_article_cache(article.title)
    try:
        search.index_article(article)
    except Exception:
        pass
    cache_article(article)
    return article_to_schema(article)


@app.get("/api/article/{article_id}/history", response_model=list[RevisionOut])
def article_history(article_id: int, db: Session = Depends(get_db)) -> list[RevisionOut]:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    revisions = (
        db.query(ArticleRevision)
        .options(selectinload(ArticleRevision.user))
        .filter(ArticleRevision.article_id == article_id)
        .order_by(ArticleRevision.created_at.desc())
        .all()
    )
    return [
        RevisionOut(
            id=revision.id,
            article_id=revision.article_id,
            user_id=revision.user_id,
            username=revision.user.username if revision.user else None,
            content=revision.content,
            edit_summary=revision.edit_summary,
            created_at=revision.created_at,
        )
        for revision in revisions
    ]


@app.get("/api/article/{article_id}/talk", response_model=list[TalkMessageOut])
def get_talk(article_id: int, db: Session = Depends(get_db)) -> list[TalkMessageOut]:
    messages = (
        db.query(TalkMessage)
        .options(selectinload(TalkMessage.user))
        .filter(TalkMessage.article_id == article_id)
        .order_by(TalkMessage.created_at.asc())
        .all()
    )
    return [
        TalkMessageOut(
            id=msg.id,
            article_id=msg.article_id,
            username=msg.user.username if msg.user else None,
            body=msg.body,
            created_at=msg.created_at,
        )
        for msg in messages
    ]

@app.post("/api/article/{article_id}/talk", response_model=TalkMessageOut, status_code=status.HTTP_201_CREATED)
def create_talk_message(
    article_id: int,
    payload: TalkMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TalkMessageOut:
    if db.get(Article, article_id) is None:
        raise HTTPException(status_code=404, detail="Article not found")
    message = TalkMessage(article_id=article_id, user_id=current_user.id, body=payload.body)
    db.add(message)
    db.commit()
    db.refresh(message)
    return TalkMessageOut(
        id=message.id,
        article_id=message.article_id,
        username=current_user.username,
        body=message.body,
        created_at=message.created_at,
    )


@app.get("/api/article/{article_id}/protection", response_model=PageProtectionOut | None)
def article_protection(article_id: int, db: Session = Depends(get_db)) -> PageProtectionOut | None:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    protection = db.query(PageProtection).filter(PageProtection.article_id == article_id).first()
    if protection is None:
        return None
    return PageProtectionOut(
        id=protection.id,
        article_id=article.id,
        title=article.title,
        level=protection.level,
        reason=protection.reason,
        expires_at=protection.expires_at,
        created_at=protection.created_at,
    )


@app.put("/api/article/{article_id}/protection", response_model=PageProtectionOut)
def protect_article(
    article_id: int,
    payload: PageProtectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PageProtectionOut:
    if current_user.role not in {"admin", "sysop"}:
        raise HTTPException(status_code=403, detail="Admin role required")
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    protection = db.query(PageProtection).filter(PageProtection.article_id == article_id).first()
    if protection is None:
        protection = PageProtection(article_id=article_id)
        db.add(protection)
    protection.level = payload.level
    protection.reason = payload.reason
    protection.expires_at = payload.expires_at
    db.commit()
    db.refresh(protection)
    return PageProtectionOut(
        id=protection.id,
        article_id=article.id,
        title=article.title,
        level=protection.level,
        reason=protection.reason,
        expires_at=protection.expires_at,
        created_at=protection.created_at,
    )


@app.delete("/api/article/{article_id}/protection", status_code=status.HTTP_204_NO_CONTENT)
def unprotect_article(
    article_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if current_user.role not in {"admin", "sysop"}:
        raise HTTPException(status_code=403, detail="Admin role required")
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    protection = db.query(PageProtection).filter(PageProtection.article_id == article_id).first()
    if protection:
        db.delete(protection)
        db.commit()


@app.get("/api/category/{category_name}/members", response_model=list[CategoryMemberOut])
def category_members(category_name: str, db: Session = Depends(get_db)) -> list[CategoryMemberOut]:
    category_slug = slugify(category_name.replace("Category:", "").strip())
    category = db.query(Category).filter(Category.slug == category_slug).first()
    if not category:
        return []
    
    articles = category.articles
    return [CategoryMemberOut(id=article.id, title=article.title) for article in articles]

@app.get("/api/article/{article_id}/backlinks", response_model=list[BacklinkOut])
def article_backlinks(article_id: int, db: Session = Depends(get_db)) -> list[BacklinkOut]:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    title = article.title
    linked_articles = (
        db.query(Article)
        .join(ArticleLink, ArticleLink.source_article_id == Article.id)
        .filter(ArticleLink.target_title == title)
        .order_by(Article.updated_at.desc())
        .limit(50)
        .all()
    )
    redirect_rows = db.query(Redirect).filter(Redirect.target_title == title).limit(50).all()
    results = [BacklinkOut(id=item.id, title=item.title, source="article-link") for item in linked_articles]
    results.extend(BacklinkOut(id=item.id, title=item.source_title, source="redirect") for item in redirect_rows)
    return results


@app.get("/api/article/{article_id}/info", response_model=PageInfoOut)
def article_info(article_id: int, db: Session = Depends(get_db)) -> PageInfoOut:
    article = db.query(Article).options(selectinload(Article.categories)).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    revision_count = db.query(ArticleRevision).filter(ArticleRevision.article_id == article_id).count()
    return PageInfoOut(
        id=article.id,
        page_id=article.page_id,
        title=article.title,
        word_count=article.word_count,
        is_user_created=article.is_user_created,
        revision_count=revision_count,
        categories=[category.name for category in article.categories],
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


@app.get("/api/article/{title:path}", response_model=ArticleOut)
def get_article(title: str, db: Session = Depends(get_db)) -> ArticleOut:
    normalized = normalize_title(title)
    try:
        cached = redis_client.get(cache_key_for_title(normalized))
        if cached:
            return ArticleOut(**json.loads(cached))
    except RedisError:
        pass

    article = (
        db.query(Article)
        .options(selectinload(Article.categories))
        .filter(Article.title == normalized)
        .first()
    )
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    cache_article(article)
    return article_to_schema(article)


@app.post("/api/admin/maintenance/rebuild-index", status_code=status.HTTP_202_ACCEPTED)
def rebuild_index(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if current_user.role not in {"admin", "sysop"}:
        raise HTTPException(status_code=403, detail="Admin role required")
    
    def run_rebuild() -> None:
        with SessionLocal() as db_session:
            articles = db_session.query(Article).all()
            for article in articles:
                try:
                    search.index_article(article)
                except Exception:
                    pass
    
    background_tasks.add_task(run_rebuild)
    return {"message": "Rebuilding index in background"}


@app.post("/api/admin/maintenance/refresh-links", status_code=status.HTTP_202_ACCEPTED)
def refresh_links(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if current_user.role not in {"admin", "sysop"}:
        raise HTTPException(status_code=403, detail="Admin role required")
    
    def run_refresh() -> None:
        with SessionLocal() as db_session:
            articles = db_session.query(Article).all()
            for article in articles:
                links = extract_links(article.content)
                sync_links(db_session, article.id, links)
            db_session.commit()
    
    background_tasks.add_task(run_refresh)
    return {"message": "Refreshing links in background"}


@app.get("/api/action")
def action_api(
    action: str = Query("query"),
    titles: str = Query(None),
    db: Session = Depends(get_db)
) -> dict:
    if action == "query" and titles:
        normalized_titles = [normalize_title(t.strip()) for t in titles.split("|") if t.strip()]
        articles = db.query(Article).filter(Article.title.in_(normalized_titles)).all()
        pages = {}
        for idx, title in enumerate(normalized_titles):
            article = next((a for a in articles if a.title == title), None)
            if article:
                pages[str(article.page_id or article.id)] = {
                    "pageid": article.page_id or article.id,
                    "ns": 0,
                    "title": article.title,
                    "extract": article.content[:500] + "..." if len(article.content) > 500 else article.content
                }
            else:
                pages[str(-1 - idx)] = {"ns": 0, "title": title, "missing": ""}
        return {"batchcomplete": "", "query": {"pages": pages}}
    return {"error": {"code": "unknown_action", "info": "Unrecognized action."}}
