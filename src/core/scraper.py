import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from .constants import TRUSTED_SOURCES, GOOGLE_NEWS_SOURCES, TELECOM_KEYWORDS, SOURCE_QUOTAS

NEWS_CACHE_FILE = "/tmp/news_cache.json"
news_cache = {}

def load_news_cache():
    global news_cache
    if os.path.exists(NEWS_CACHE_FILE):
        try:
            with open(NEWS_CACHE_FILE) as f:
                news_cache = json.load(f)
        except:
            news_cache = {}

def save_news_cache():
    with open(NEWS_CACHE_FILE, 'w') as f:
        json.dump(news_cache, f)

load_news_cache()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def news_relevance(text):
    text_lower = text.lower()
    score = 0
    for kw in TELECOM_KEYWORDS:
        if kw in text_lower:
            score += 1
    if any(term in text_lower for term in ["network", "telecom", "internet", "fiber", "spectrum", "satellite", "cyber", "btrc"]):
        score += 2
    if any(term in text_lower for term in ["defense", "defence", "army", "navy", "air force", "border", "security"]):
        score += 1
    return score

def add_news_result(results, item):
    item.setdefault("category", "News")
    item.setdefault("relevance", news_relevance(item.get("headline", "")))
    if item["relevance"] <= 0:
        return
    category = item.get("category", "News")
    current_count = sum(1 for r in results if r.get("category") == category)
    if current_count >= SOURCE_QUOTAS.get(category, 2):
        return
    results.append(item)

def scrape_news(district_name, division_name):
    cache_key = f"intel_v2_{district_name}_{datetime.now().strftime('%Y-%m-%d')}"
    if cache_key in news_cache and len(news_cache[cache_key]) > 0:
        return news_cache[cache_key]

    results = []
    search_terms = [
        district_name.lower(), division_name.lower(),
        "bangladesh digital", "bangladesh telecom", "btrc", "internet bangladesh",
        "mobile internet", "broadband", "digital divide", "connectivity",
        "defense", "defence", "cyber", "satellite", "submarine cable", "spectrum",
    ]

    for source in TRUSTED_SOURCES:
        try:
            resp = requests.get(source["url"], headers=HEADERS, timeout=8, verify=False)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "a", "p", "span", "li", "td"])
            seen_texts = set()
            for tag in tags[:220]:
                text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))
                if len(text) < 18 or len(text) > 260 or text in seen_texts:
                    continue
                seen_texts.add(text)
                text_lower = text.lower()
                if not (any(kw in text_lower for kw in TELECOM_KEYWORDS) or any(t in text_lower for t in search_terms)):
                    continue
                href = tag.get("href") if tag.name == "a" else None
                add_news_result(results, {
                    "headline": text[:220],
                    "source": source["name"],
                    "tier": source["tier"],
                    "category": source["category"],
                    "url": urljoin(source["url"], href) if href else source["url"],
                    "scraped_at": datetime.now().strftime("%Y-%m-%d"),
                })
                break
        except Exception as e:
            print(f"News scrape error {source['name']}: {e}")
            continue

    if len(results) < 8:
        for source in GOOGLE_NEWS_SOURCES:
            try:
                resp = requests.get(source["url"], headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "xml")
                for item in soup.find_all("item")[:12]:
                    title = item.find("title")
                    if not title:
                        continue
                    text = re.sub(r"\s+", " ", title.get_text(" ", strip=True))
                    if len(text) < 15 or len(text) > 260:
                        continue
                    text_lower = text.lower()
                    if not (any(kw in text_lower for kw in TELECOM_KEYWORDS) or any(t in text_lower for t in search_terms)):
                        continue
                    link = item.find("link")
                    add_news_result(results, {
                        "headline": text[:220],
                        "source": source["name"],
                        "tier": source["tier"],
                        "category": source["category"],
                        "url": link.get_text(strip=True) if link else source["url"],
                        "scraped_at": datetime.now().strftime("%Y-%m-%d"),
                    })
            except Exception as e:
                print(f"Google News RSS error {source['name']}: {e}")
                continue

    seen = set()
    deduped = []
    for r in results:
        key = (re.sub(r"\W+", "", r["headline"].lower())[:120], r.get("source", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    if len(deduped) < 3:
        deduped.append({
            "headline": f"Live source coverage was limited for {district_name}; monitor BTRC notices, bdnews24 telecom reports, and regional defense/cyber decisions before final network planning.",
            "source": "Connectiva Monitor",
            "tier": 2,
            "category": "Monitoring",
            "url": "https://btrc.gov.bd/",
            "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            "relevance": 1,
        })

    deduped.sort(key=lambda x: (x.get("tier", 3), -x.get("relevance", 0), x.get("source", "")))
    final = deduped[:8]
    news_cache[cache_key] = final
    save_news_cache()
    return final
