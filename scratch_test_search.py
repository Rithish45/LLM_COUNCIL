import asyncio
import httpx
import urllib.parse
from bs4 import BeautifulSoup

async def search_evidence(query: str, max_results: int = 3) -> list:
    clean_query = query.strip()
    # Strip long conversational filler, keep essential keywords up to 100 chars
    if len(clean_query) > 100:
        words = [w for w in clean_query.split() if w.lower() not in ['should', 'governments', 'impose', 'essential', 'consumer', 'during']]
        clean_query = " ".join(words[:8])

    headers = {
        'User-Agent': 'LLMCouncilFactChecker/1.0 (https://github.com/llm-council; factchecker@llmcouncil.org)',
        'Accept': 'application/json'
    }
    results = []

    # Strategy 1: Wikipedia Search API
    try:
        async with httpx.AsyncClient(headers=headers, timeout=6.0, follow_redirects=True) as client:
            resp = await client.get('https://en.wikipedia.org/w/api.php', params={
                'action': 'query',
                'list': 'search',
                'srsearch': clean_query,
                'format': 'json',
                'srlimit': max_results
            })
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('query', {}).get('search', []):
                    title = item.get('title')
                    snippet = BeautifulSoup(item.get('snippet', ''), 'html.parser').get_text()
                    url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    results.append({
                        'title': f"Wikipedia: {title}",
                        'snippet': snippet,
                        'url': url
                    })
    except Exception as e:
        print(f"Wiki search error: {e}")

    # Strategy 2: Fallback DuckDuckGo Lite if Wiki returned empty
    if not results:
        try:
            ddg_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            }
            async with httpx.AsyncClient(headers=ddg_headers, timeout=6.0, follow_redirects=True) as client:
                resp = await client.get('https://html.duckduckgo.com/html/', params={'q': clean_query})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for res in soup.select('.result'):
                        t_node = res.select_one('.result__title a')
                        s_node = res.select_one('.result__snippet')
                        if t_node and s_node:
                            results.append({
                                'title': t_node.get_text(strip=True),
                                'snippet': s_node.get_text(strip=True),
                                'url': t_node.get('href', '')
                            })
                            if len(results) >= max_results:
                                break
        except Exception as e:
            print(f"DDG search error: {e}")

    return results

async def main():
    test_queries = [
        "price controls economic instability shortages",
        "price controls black markets economy",
        "price controls inflation history"
    ]
    for q in test_queries:
        print(f"\nQuery: '{q}'")
        res = await search_evidence(q)
        print(f"Results returned: {len(res)}")
        for r in res:
            print(f"  • Title: {r['title']}")
            print(f"    URL:   {r['url']}")
            print(f"    Snip:  {r['snippet'][:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
