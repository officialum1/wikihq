# MediaWiki Feature Map

This project is intentionally not a line-for-line clone of MediaWiki. MediaWiki is a mature wiki engine with a large core, skins, extensions, maintenance scripts, API surfaces, language support, and operational tooling. This map tracks the MediaWiki-style features we are adding to this platform.

## Implemented Core Batch

| MediaWiki-style feature | Local implementation |
| --- | --- |
| Read article pages | `/wiki/[title]` |
| Edit article pages | `/wiki/[title]/edit` |
| Page history | `/wiki/[title]/history` |
| Categories in sidebar | `categories` and `article_categories` tables |
| Search | `/search` and `GET /api/search` |
| Special pages index | `/special` and `GET /api/special/pages` |
| Recent changes | `/special/recent-changes` and `GET /api/recent-changes` |
| Random article | `/special/random` and `GET /api/random` |
| Page information | `/wiki/[title]/info` and `GET /api/article/{id}/info` |
| Import progress special/admin page | `/admin/progress` and `GET /api/progress` |
| User registration/login | `/auth/register`, `/auth/login`, JWT |
| Skin-like navigation and toolbox | top navigation plus article sidebar tools |
| Discussion pages | `/wiki/[title]/talk` and `GET/POST /api/article/{id}/talk` |
| Watchlist | `/special/watchlist` and `GET/POST /api/watchlist` |
| Namespaces | `/special/namespaces` and `GET /api/namespaces` |
| Page protection | `/wiki/[title]/protect` and `GET/PUT /api/article/{id}/protection` |
| Redirects | `/special/redirects` and `GET/POST /api/redirects` |
| What links here | `/wiki/[title]/backlinks` and `GET /api/article/{id}/backlinks` |
| File pages/uploads metadata | `/special/files` and `GET/POST /api/files` |
| Templates | `/special/templates` and `GET/POST /api/templates` |
| Patrol queue | `/special/patrol` and `GET /api/patrol` |
| Site statistics | `/special/statistics` and `GET /api/statistics` |

## Next Feature Groups

1. Threaded discussion UI, signatures, archiving, and talk namespace title parsing.
2. Real upload storage, file thumbnails, file revisions, and media rendering.
3. Template expansion, transclusion, parser functions, and dependency tracking.
4. Link tables for broken links, external links, double redirects, and page move history.
5. User groups, granular permissions, edit locks, abuse throttles, and blocks.
6. Watch/unwatch buttons inside article actions and notification filters.
7. Diff viewer, rollback, patrol status mutation, and moderation logs.
8. Language/i18n message catalog, interlanguage links, and RTL layout support.
9. Maintenance jobs: rebuild search index, refresh link tables, cleanup scripts.
10. API compatibility: action-like endpoints and richer REST resources.
11. Skins/extensions model: plugin registry, skin metadata, hooks, feature flags.
12. Importer parity: redirects, templates, file metadata, categories, and link graph extraction from dumps.
