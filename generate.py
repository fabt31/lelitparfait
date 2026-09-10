#!/usr/bin/env python3
"""
Générateur de site LeLitParfait.fr
Lit graph.yaml et génère :
  - Pages de redirection meta-refresh (ancien /blog/ → nouvelle URL)
  - Pages hub (index de cluster avec liste des spokes)
  - Pages stub pour les spokes planifiés
  - JSON-LD unifié sur toutes les pages publiées
  - sitemap.xml

Usage : python3 generate.py [--graph graph.yaml] [--dry-run]
"""

import argparse, yaml, os, re, shutil
from datetime import date
from pathlib import Path
from html import escape

# ── Config ──────────────────────────────────────────────────────────────────
SITE_URL   = "https://lelitparfait.fr"
BUILD_DIR  = Path(__file__).parent   # génère dans le repo lui-même
TODAY      = date.today().isoformat()
AFFILIATE_NOTICE = (
    '<p class="affiliate-notice">'
    '<em>En tant que Partenaire Amazon, je réalise un bénéfice sur les '
    'achats remplissant les conditions requises.</em></p>'
)

# ── Helpers ─────────────────────────────────────────────────────────────────

def load_graph(path="graph.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def url_to_path(url: str) -> Path:
    """'/matelas/mousse/' → BUILD_DIR/matelas/mousse/index.html"""
    parts = url.strip("/").split("/")
    if not parts or parts == [""]:
        return BUILD_DIR / "index.html"
    return BUILD_DIR / Path(*parts) / "index.html"

def breadcrumb_chain(node_id: str, nodes: dict) -> list:
    chain, seen = [], set()
    current = node_id
    while current and current not in seen:
        seen.add(current)
        n = nodes[current]
        chain.append({"name": n["title"], "url": n["url"], "id": current})
        current = n.get("parent")
    chain.reverse()
    return chain

def breadcrumb_jsonld(chain: list) -> str:
    items = []
    for i, item in enumerate(chain, 1):
        items.append(
            f'{{"@type":"ListItem","position":{i},'
            f'"name":{_js(item["name"])},'
            f'"item":"{SITE_URL}{item["url"]}"}}'
        )
    return (
        '{"@type":"BreadcrumbList",'
        f'"@id":"{SITE_URL}{chain[-1]["url"]}#breadcrumb",'
        '"itemListElement":[' + ",".join(items) + "]}"
    )

def related_nodes(node: dict, nodes: dict) -> list:
    return [
        {"anchor": r["anchor"], "url": nodes[r["to"]]["url"],
         "title": nodes[r["to"]]["title"]}
        for r in (node.get("related") or [])
        if r["to"] in nodes
    ]

def children_of(node_id: str, nodes: dict) -> list:
    return [n for n in nodes.values() if n.get("parent") == node_id]

def _js(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

# ── HTML Partials ────────────────────────────────────────────────────────────

HEAD_CSS = """\
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/assets/fonts.css">
<style>
:root{--night:#0B1120;--moon:#F4E9D8;--moon-soft:#FBF5EC;--star:#D4AF37;
--sleep-blue:#5B7DB1;--gray-100:#F7F5F2;--gray-200:#EDE8E2;--gray-500:#8A8278;
--gray-700:#4A4540;--radius:12px;--shadow:0 4px 24px rgba(11,17,32,.08);}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'DM Sans',sans-serif;color:var(--gray-700);
background:var(--moon-soft);line-height:1.8;font-size:17px}
.container{max-width:860px;margin:0 auto;padding:0 24px}
h1,h2,h3{font-family:'Playfair Display',serif;color:var(--night);line-height:1.3}
nav.site-nav{background:rgba(251,245,236,.95);backdrop-filter:blur(12px);
padding:14px 0;box-shadow:var(--shadow);position:sticky;top:0;z-index:100}
nav.site-nav .container{display:flex;align-items:center;justify-content:space-between}
.nav-logo{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;
color:var(--night);text-decoration:none}
.page-hero{background:linear-gradient(135deg,var(--night),#1E2D56);
padding:80px 0 40px;color:var(--moon);text-align:center}
.page-hero h1{font-size:2rem;margin-bottom:12px;color:var(--moon);max-width:680px;
margin-left:auto;margin-right:auto}
.page-content{padding:48px 0 80px}
.page-content h2{font-size:1.5rem;margin:36px 0 14px}
.page-content p{margin-bottom:16px}
.breadcrumb{font-size:0.82rem;color:var(--gray-500);margin-bottom:32px}
.breadcrumb a{color:var(--sleep-blue);text-decoration:none}
.breadcrumb span{margin:0 6px}
.hub-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
gap:20px;margin:28px 0}
.hub-card{background:#fff;border-radius:var(--radius);box-shadow:var(--shadow);
padding:24px;text-decoration:none;color:inherit;transition:.2s}
.hub-card:hover{box-shadow:0 8px 32px rgba(11,17,32,.14);transform:translateY(-2px)}
.hub-card h3{font-size:1rem;color:var(--night);margin-bottom:8px}
.hub-card p{font-size:0.85rem;color:var(--gray-500);line-height:1.5}
.related-box{background:var(--gray-100);border-radius:var(--radius);
padding:24px;margin:40px 0}
.related-box h3{font-size:1rem;margin-bottom:12px;color:var(--night)}
.related-box ul{list-style:none}
.related-box li{margin-bottom:8px}
.related-box a{color:var(--sleep-blue);text-decoration:none;font-size:0.9rem}
.affiliate-notice{font-size:0.78rem;color:var(--gray-500);text-align:center;margin:16px 0}
footer.site-footer{background:var(--night);color:var(--moon);padding:32px 0;
text-align:center;font-size:0.82rem;opacity:.7}
footer.site-footer a{color:var(--star);text-decoration:none}
</style>"""

def nav_html():
    return (
        '<nav class="site-nav"><div class="container">'
        f'<a class="nav-logo" href="/">🌙 LeLitParfait.fr</a>'
        '<div style="display:flex;gap:20px;font-size:0.88rem">'
        '<a href="/matelas/" style="color:var(--sleep-blue)">Matelas</a>'
        '<a href="/oreillers/" style="color:var(--sleep-blue)">Oreillers</a>'
        '<a href="/entretien/" style="color:var(--sleep-blue)">Entretien</a>'
        '<a href="/acheter-un-matelas/" style="color:var(--sleep-blue)">Vos droits</a>'
        '</div></div></nav>'
    )

def footer_html():
    return (
        '<footer class="site-footer"><div class="container">'
        '<p>En tant que Partenaire Amazon, je réalise un bénéfice sur les achats '
        'remplissant les conditions requises.</p>'
        '<p style="margin-top:8px">'
        '<a href="/mentions-legales.html">Mentions légales</a> · '
        '<a href="/politique-confidentialite.html">Confidentialité</a>'
        '</p></div></footer>'
    )

def breadcrumb_html(chain: list) -> str:
    parts = []
    for i, item in enumerate(chain):
        if i < len(chain) - 1:
            parts.append(f'<a href="{item["url"]}">{escape(item["name"])}</a>')
        else:
            parts.append(f'<span>{escape(item["name"])}</span>')
    return '<nav class="breadcrumb">' + ' <span>›</span> '.join(parts) + '</nav>'

def jsonld_graph(node: dict, nodes: dict, chain: list, site: dict) -> str:
    author = site.get("author", {})
    org = site.get("publisher", {})
    url = SITE_URL + node["url"]

    organization = (
        f'{{"@type":"Organization","@id":"{SITE_URL}/#organization",'
        f'"name":{_js(org.get("name","LeLitParfait.fr"))},'
        f'"url":"{SITE_URL}"}}'
    )
    person = (
        f'{{"@type":"Person","@id":"{SITE_URL}/#author",'
        f'"name":{_js(author.get("name","Angélina Saglietti"))},'
        f'"url":"{SITE_URL}/a-propos/"}}'
    )
    webpage = (
        f'{{"@type":"WebPage","@id":"{url}#webpage",'
        f'"url":"{url}",'
        f'"name":{_js(node["title"])},'
        f'"isPartOf":{{"@id":"{SITE_URL}/#website"}},'
        f'"dateModified":"{TODAY}",'
        f'"breadcrumb":{{"@id":"{url}#breadcrumb"}}}}'
    )
    website = (
        f'{{"@type":"WebSite","@id":"{SITE_URL}/#website",'
        f'"url":"{SITE_URL}",'
        f'"name":"LeLitParfait.fr",'
        f'"publisher":{{"@id":"{SITE_URL}/#organization"}}}}'
    )
    bc = breadcrumb_jsonld(chain)

    same_as = node.get("sameAs", [])
    article_extra = ""
    if same_as:
        sa_list = ",".join(f'"{u}"' for u in same_as)
        article_extra = f',"about":{{"@type":"Thing","sameAs":[{sa_list}]}}'

    ntype = node.get("type", "spoke")
    if ntype in ("spoke", "comparatif", "glossaire"):
        page_entity = (
            f'{{"@type":"Article","@id":"{url}#article",'
            f'"headline":{_js(node["title"])},'
            f'"url":"{url}",'
            f'"dateModified":"{TODAY}",'
            f'"author":{{"@id":"{SITE_URL}/#author"}},'
            f'"publisher":{{"@id":"{SITE_URL}/#organization"}}'
            f'{article_extra}}}'
        )
    else:
        page_entity = None

    graph_items = [organization, person, website, webpage, bc]
    if page_entity:
        graph_items.append(page_entity)

    return (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@graph":['
        + ",".join(graph_items)
        + "]}</script>"
    )

# ── Page generators ──────────────────────────────────────────────────────────

def make_redirect_page(old_url: str, new_url: str) -> str:
    full_new = SITE_URL + new_url
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url={full_new}">
<link rel="canonical" href="{full_new}">
<title>Redirection…</title>
</head>
<body>
<p>Cette page a déménagé : <a href="{full_new}">{full_new}</a></p>
</body>
</html>"""

def make_hub_page(node: dict, nodes: dict, chain: list, site: dict) -> str:
    children = children_of(node["id"], nodes)
    children.sort(key=lambda n: n.get("intent", "info"))

    cards = ""
    for child in children:
        intent_badge = {"transactionnel": "💰", "commercial": "🛒", "info": "📖"}.get(
            child.get("intent", "info"), ""
        )
        cards += (
            f'<a class="hub-card" href="{child["url"]}">'
            f'<h3>{intent_badge} {escape(child["title"])}</h3>'
            f'<p>{escape(child.get("cluster",""))} · {child.get("intent","info")}</p>'
            "</a>"
        )

    related = related_nodes(node, nodes)
    related_html = ""
    if related:
        items = "".join(
            f'<li><a href="{r["url"]}">{escape(r["anchor"])}</a></li>'
            for r in related
        )
        related_html = (
            '<div class="related-box">'
            "<h3>À lire aussi</h3><ul>" + items + "</ul></div>"
        )

    bc_html = breadcrumb_html(chain)
    jld = jsonld_graph(node, nodes, chain, site)
    title = node["title"]

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
{HEAD_CSS}
<title>{escape(title)} — LeLitParfait.fr</title>
<meta name="description" content="{escape(title)}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:url" content="{SITE_URL}{node['url']}">
<meta property="og:image" content="{SITE_URL}/assets/img/matelas-hybride.jpg">
<link rel="canonical" href="{SITE_URL}{node['url']}">
{jld}
</head>
<body>
{nav_html()}
<div class="page-hero"><div class="container"><h1>{escape(title)}</h1></div></div>
<main class="page-content"><div class="container">
{bc_html}
<div class="hub-grid">{cards}</div>
{related_html}
</div></main>
{footer_html()}
</body>
</html>"""

def make_stub_page(node: dict, nodes: dict, chain: list, site: dict) -> str:
    related = related_nodes(node, nodes)
    related_html = ""
    if related:
        items = "".join(
            f'<li><a href="{r["url"]}">{escape(r["anchor"])}</a></li>'
            for r in related
        )
        related_html = (
            '<div class="related-box"><h3>À lire aussi</h3><ul>'
            + items + "</ul></div>"
        )

    bc_html = breadcrumb_html(chain)
    jld = jsonld_graph(node, nodes, chain, site)
    title = node["title"]

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
{HEAD_CSS}
<title>{escape(title)} — LeLitParfait.fr</title>
<meta name="description" content="{escape(title)}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:url" content="{SITE_URL}{node['url']}">
<meta property="og:image" content="{SITE_URL}/assets/img/matelas-hybride.jpg">
<link rel="canonical" href="{SITE_URL}{node['url']}">
{jld}
</head>
<body>
{nav_html()}
<div class="page-hero"><div class="container">
<h1>{escape(title)}</h1>
</div></div>
<main class="page-content"><div class="container">
{bc_html}
<p><em>Article en cours de rédaction — revenez bientôt.</em></p>
{related_html}
</div></main>
{footer_html()}
</body>
</html>"""

def inject_jsonld_breadcrumb(html: str, node: dict, nodes: dict,
                              chain: list, site: dict) -> str:
    """Injecte JSON-LD + og:image + canonical dans un HTML existant."""
    jld = jsonld_graph(node, nodes, chain, site)
    bc_html = breadcrumb_html(chain)
    url = SITE_URL + node["url"]

    # Remove old ld+json blocks
    html = re.sub(
        r'<script type=["\']application/ld\+json["\']>.*?</script>',
        "", html, flags=re.DOTALL
    )
    # Inject new ld+json before </head>
    html = html.replace("</head>", jld + "\n</head>", 1)

    # Add og:image if missing
    if 'og:image' not in html:
        html = html.replace(
            "</head>",
            f'<meta property="og:image" content="{SITE_URL}/assets/img/matelas-hybride.jpg">\n</head>',
            1
        )

    # Add canonical if missing
    if 'rel="canonical"' not in html:
        html = html.replace(
            "</head>",
            f'<link rel="canonical" href="{url}">\n</head>',
            1
        )

    # Inject breadcrumb after first <main> or after <header class="article-hero">
    if 'class="breadcrumb"' not in html:
        html = re.sub(
            r'(<(?:main|div)[^>]*class="[^"]*(?:article-content|page-content)[^"]*"[^>]*>)',
            r'\1\n' + bc_html,
            html, count=1
        )

    # Replace external font link if somehow remaining
    html = re.sub(
        r'<link[^>]*fonts\.googleapis\.com[^>]*>',
        '<link rel="stylesheet" href="/assets/fonts.css">',
        html
    )

    return html

# ── Sitemap ──────────────────────────────────────────────────────────────────

def make_sitemap(nodes: dict) -> str:
    urls = []
    for n in nodes.values():
        priority = {"home": "1.0", "hub": "0.8", "comparatif": "0.7",
                    "spoke": "0.6", "glossaire": "0.5"}.get(n.get("type","spoke"), "0.6")
        urls.append(
            f"  <url>\n"
            f"    <loc>{SITE_URL}{n['url']}</loc>\n"
            f"    <lastmod>{TODAY}</lastmod>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", default="graph.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data  = load_graph(args.graph)
    nodes = {n["id"]: n for n in data["nodes"]}
    site  = data["site"]

    created, patched, redirects = 0, 0, 0

    for nid, node in nodes.items():
        chain  = breadcrumb_chain(nid, nodes)
        status = node.get("status", "planned")
        ntype  = node.get("type", "spoke")
        dest   = url_to_path(node["url"])

        # ── 1. Redirection pages (redirect_from) ──────────────────────────
        redir_from = node.get("redirect_from") or []
        if isinstance(redir_from, str):
            redir_from = [redir_from]
        for old_url in redir_from:
            old_path = BUILD_DIR / old_url.lstrip("/")
            redir    = make_redirect_page(old_url, node["url"])
            if not args.dry_run:
                old_path.parent.mkdir(parents=True, exist_ok=True)
                old_path.write_text(redir, encoding="utf-8")
            print(f"  REDIRECT {old_url} → {node['url']}")
            redirects += 1

        # ── 2. Published pages → patch JSON-LD in existing HTML ───────────
        if status == "published":
            # For home, the file is index.html at root
            existing = dest
            if existing.exists():
                html = existing.read_text(encoding="utf-8")
                html = inject_jsonld_breadcrumb(html, node, nodes, chain, site)
                if not args.dry_run:
                    existing.write_text(html, encoding="utf-8")
                print(f"  PATCH    {node['url']} ({existing.relative_to(BUILD_DIR)})")
                patched += 1
            else:
                # Need to create directory + copy from existing location
                # (hub pages like meilleurs-matelas that will eventually live at /matelas/meilleurs-matelas-2026/)
                if not args.dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                # For now generate a stub (content migration is a separate step)
                if ntype == "hub":
                    page = make_hub_page(node, nodes, chain, site)
                else:
                    page = make_stub_page(node, nodes, chain, site)
                if not args.dry_run:
                    dest.write_text(page, encoding="utf-8")
                print(f"  CREATE   {node['url']} (stub, content to migrate)")
                created += 1

        # ── 3. Planned pages → generate hub or stub ───────────────────────
        elif status == "planned":
            if dest.exists():
                continue  # don't overwrite manually created pages
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
            if ntype == "hub":
                page = make_hub_page(node, nodes, chain, site)
            else:
                page = make_stub_page(node, nodes, chain, site)
            if not args.dry_run:
                dest.write_text(page, encoding="utf-8")
            print(f"  CREATE   {node['url']} [{ntype}]")
            created += 1

    # ── Sitemap ──────────────────────────────────────────────────────────────
    sitemap = make_sitemap(nodes)
    if not args.dry_run:
        (BUILD_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"\n  SITEMAP  sitemap.xml ({len(nodes)} URLs)")

    print(f"\n✓ Done — {created} créées · {patched} patchées · {redirects} redirections")

if __name__ == "__main__":
    main()
