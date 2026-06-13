from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    username_or_email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime


class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)
    edit_summary: str = Field(default="Created article", max_length=500)
    categories: list[str] = Field(default_factory=list)


class ArticleUpdate(BaseModel):
    content: str = Field(min_length=1)
    edit_summary: str = Field(default="Updated article", max_length=500)
    categories: list[str] | None = None


class ArticleOut(BaseModel):
    id: int
    page_id: int | None
    title: str
    content: str
    html_content: str
    word_count: int
    is_user_created: bool
    categories: list[str]
    interlanguage_links: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RevisionOut(BaseModel):
    id: int
    article_id: int
    user_id: int | None
    username: str | None
    content: str
    edit_summary: str
    created_at: datetime


class ProgressOut(BaseModel):
    id: int
    last_page_id: int
    total_imported: int
    status: str
    updated_at: datetime


class SearchResult(BaseModel):
    id: int
    title: str
    snippet: str
    word_count: int
    updated_at: datetime


class SearchResponse(BaseModel):
    query: str
    page: int
    page_size: int
    total: int
    results: list[SearchResult]


class RecentChangeOut(BaseModel):
    id: int
    article_id: int
    title: str
    username: str | None
    edit_summary: str
    created_at: datetime


class PageInfoOut(BaseModel):
    id: int
    page_id: int | None
    title: str
    word_count: int
    is_user_created: bool
    revision_count: int
    categories: list[str]
    created_at: datetime
    updated_at: datetime


class SpecialPageOut(BaseModel):
    title: str
    path: str
    description: str
    section: str


class NamespaceOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str


class TalkMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class TalkMessageOut(BaseModel):
    id: int
    article_id: int
    username: str | None
    body: str
    created_at: datetime


class WatchlistItemOut(BaseModel):
    id: int
    article_id: int
    title: str
    created_at: datetime


class PageProtectionCreate(BaseModel):
    level: str = Field(default="autoconfirmed", max_length=50)
    reason: str = Field(default="", max_length=500)
    expires_at: datetime | None = None


class PageProtectionOut(BaseModel):
    id: int
    article_id: int
    title: str
    level: str
    reason: str
    expires_at: datetime | None
    created_at: datetime


class RedirectCreate(BaseModel):
    source_title: str = Field(min_length=1, max_length=512)
    target_title: str = Field(min_length=1, max_length=512)


class RedirectOut(BaseModel):
    id: int
    source_title: str
    target_title: str
    created_at: datetime


class CategoryMemberOut(BaseModel):
    id: int
    title: str

class BacklinkOut(BaseModel):
    id: int
    title: str
    source: str


class FileAssetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(default="application/octet-stream", max_length=120)
    size_bytes: int = Field(default=0, ge=0)
    description: str = ""


class FileAssetOut(BaseModel):
    id: int
    title: str
    filename: str
    mime_type: str
    size_bytes: int
    description: str
    uploader: str | None
    created_at: datetime


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    description: str = Field(default="", max_length=500)


class TemplateOut(BaseModel):
    id: int
    name: str
    content: str
    description: str
    created_at: datetime
    updated_at: datetime


class PatrolItemOut(BaseModel):
    revision_id: int
    article_id: int
    title: str
    username: str | None
    status: str
    edit_summary: str
    created_at: datetime


class StatisticsOut(BaseModel):
    articles: int
    users: int
    revisions: int
    categories: int
    files: int
    templates: int
