from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


article_categories = Table(
    "article_categories",
    Base.metadata,
    Column("article_id", ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(BigInteger, unique=True, nullable=True, index=True)
    title = Column(String(512), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    html_content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False, default=0)
    is_user_created = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    categories = relationship("Category", secondary=article_categories, back_populates="articles")
    revisions = relationship("ArticleRevision", back_populates="article", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="editor")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    revisions = relationship("ArticleRevision", back_populates="user")


class ArticleRevision(Base):
    __tablename__ = "article_revisions"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    edit_summary = Column(String(500), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    article = relationship("Article", back_populates="revisions")
    user = relationship("User", back_populates="revisions")


class ImportProgress(Base):
    __tablename__ = "import_progress"

    id = Column(Integer, primary_key=True)
    last_page_id = Column(BigInteger, nullable=False, default=0)
    total_imported = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="idle")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("slug", name="uq_categories_slug"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(255), nullable=False, index=True)

    articles = relationship("Article", secondary=article_categories, back_populates="categories")


class Namespace(Base):
    __tablename__ = "namespaces"
    __table_args__ = (UniqueConstraint("slug", name="uq_namespaces_slug"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False, index=True)
    slug = Column(String(80), nullable=False, index=True)
    description = Column(String(500), nullable=False, default="")


class TalkMessage(Base):
    __tablename__ = "talk_messages"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    article = relationship("Article")
    user = relationship("User")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_watchlist_user_article"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    article = relationship("Article")
    user = relationship("User")


class PageProtection(Base):
    __tablename__ = "page_protections"
    __table_args__ = (UniqueConstraint("article_id", name="uq_page_protection_article"),)

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String(50), nullable=False, default="autoconfirmed")
    reason = Column(String(500), nullable=False, default="")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    article = relationship("Article")


class Redirect(Base):
    __tablename__ = "redirects"
    __table_args__ = (UniqueConstraint("source_title", name="uq_redirect_source_title"),)

    id = Column(Integer, primary_key=True, index=True)
    source_title = Column(String(512), nullable=False, index=True)
    target_title = Column(String(512), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FileAsset(Base):
    __tablename__ = "file_assets"
    __table_args__ = (UniqueConstraint("title", name="uq_file_assets_title"),)

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(120), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=False, default="")
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    uploader = relationship("User")


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = (UniqueConstraint("name", name="uq_templates_name"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    description = Column(String(500), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PatrolLog(Base):
    __tablename__ = "patrol_logs"

    id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(Integer, ForeignKey("article_revisions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="unreviewed")
    note = Column(String(500), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    revision = relationship("ArticleRevision")
    user = relationship("User")


class ArticleLink(Base):
    __tablename__ = "article_links"
    __table_args__ = (UniqueConstraint("source_article_id", "target_title", name="uq_article_links"),)

    id = Column(Integer, primary_key=True, index=True)
    source_article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    target_title = Column(String(512), nullable=False, index=True)

    source_article = relationship("Article")
