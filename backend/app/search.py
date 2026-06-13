from datetime import datetime

from elasticsearch import Elasticsearch

from .config import settings
from .models import Article


INDEX_NAME = "articles"


from elasticsearch import ElasticsearchException

def get_client() -> Elasticsearch:
    if not settings.elasticsearch_url:
        raise ElasticsearchException("Elasticsearch URL is empty")
    return Elasticsearch(settings.elasticsearch_url, request_timeout=5)


def ensure_index() -> None:
    client = get_client()
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


def index_article(article: Article) -> None:
    client = get_client()
    client.index(
        index=INDEX_NAME,
        id=article.id,
        document={
            "id": article.id,
            "page_id": article.page_id,
            "title": article.title,
            "content": article.content,
            "html_content": article.html_content,
            "word_count": article.word_count,
            "updated_at": article.updated_at.isoformat() if isinstance(article.updated_at, datetime) else article.updated_at,
        },
    )


def search_articles(query: str, page: int, page_size: int) -> dict:
    client = get_client()
    from_index = (page - 1) * page_size
    response = client.search(
        index=INDEX_NAME,
        from_=from_index,
        size=page_size,
        query={
            "multi_match": {
                "query": query,
                "fields": ["title^4", "content", "html_content"],
                "type": "best_fields",
                "fuzziness": "AUTO",
            }
        },
        highlight={
            "fields": {
                "content": {"fragment_size": 180, "number_of_fragments": 1},
                "html_content": {"fragment_size": 180, "number_of_fragments": 1},
            }
        },
    )
    total_value = response["hits"]["total"]
    total = total_value["value"] if isinstance(total_value, dict) else int(total_value)
    return {"total": total, "hits": response["hits"]["hits"]}

