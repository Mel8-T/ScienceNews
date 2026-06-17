#!/usr/bin/env python3
"""
Daily Science News Fetcher für GitHub Actions
Holt ScienceDaily News, übersetzt zu Deutsch, speichert als news.json
"""

import feedparser
import json
import anthropic
from datetime import datetime
import os

# ============================================================================
# CONFIG
# ============================================================================

SCIENCEDAILY_FEED = "https://www.sciencedaily.com/rss/all.xml"
OUTPUT_FILE = "news.json"

# ============================================================================
# FETCH NEWS
# ============================================================================

def fetch_news(feed_url, limit=10):
    """Hole News von ScienceDaily RSS Feed"""
    print(f"📰 Fetching from {feed_url}...")
    
    feed = feedparser.parse(feed_url)
    
    if feed.bozo:
        print(f"⚠️ Feed warning: {feed.bozo_exception}")
    
    articles = []
    for entry in feed.entries[:limit]:
        article = {
            'title': entry.get('title', 'No title'),
            'summary': entry.get('summary', ''),
            'link': entry.get('link', ''),
            'published': entry.get('published', datetime.now().isoformat())
        }
        articles.append(article)
    
    print(f"✓ Fetched {len(articles)} articles")
    return articles

# ============================================================================
# TRANSLATE & PROCESS
# ============================================================================

def process_article(article):
    """Übersetze & kürze Artikel mit Claude"""
    
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
    
    # Clean summary
    summary = article['summary'].replace('<p>', '').replace('</p>', '')
    text = f"{article['title']}. {summary}"
    
    # Kurze Summary
    prompt_short = f"""Übersetze diesen Science-Artikel ins Deutsche in 1-2 Sätzen.
Kurz, ansprechend, mit Sog.

ORIGINAL (English):
{text}

ANTWORT (nur Deutsch, sonst nichts):"""
    
    msg_short = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt_short}]
    )
    
    summary_short = msg_short.content[0].text.strip()
    
    # Längere Summary
    prompt_long = f"""Übersetze diesen Science-Artikel ins Deutsche (3-4 Sätze).
Mit alltäglichen Wörtern, wie ein Freund erzählt.
Keine akademische Sprache.

ORIGINAL (English):
{text}

ANTWORT (nur Deutsch, sonst nichts):"""
    
    msg_long = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt_long}]
    )
    
    summary_long = msg_long.content[0].text.strip()
    
    return {
        'title_de': article['title'],
        'summary_short': summary_short,
        'summary_long': summary_long,
        'link': article['link'],
        'date': article['published'][:10]
    }

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("SCIENCE NEWS DAILY FETCHER (GitHub Actions)")
    print("="*70)
    
    # Check API Key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not set!")
        return
    
    # Fetch
    articles = fetch_news(SCIENCEDAILY_FEED, limit=10)
    
    if not articles:
        print("✗ No articles found")
        return
    
    # Process each
    processed = []
    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] Processing: {article['title'][:60]}...")
        try:
            processed_article = process_article(article)
            processed.append(processed_article)
            print(f"✓ Done")
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    # Save
    data = {
        'generated_at': datetime.now().isoformat(),
        'total': len(processed),
        'articles': processed
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved {len(processed)} articles to {OUTPUT_FILE}")
    print("="*70)

if __name__ == '__main__':
    main()
