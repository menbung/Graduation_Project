import requests
from bs4 import BeautifulSoup

def fetch_html(url: str, timeout=10):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

def crawl_lyrics(url: str) -> dict:
    html = fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.select_one('h1').get_text(strip=True) if soup.select_one('h1') else 'Unknown'
    lyrics = '\n'.join([p.get_text() for p in soup.select('.lyrics p')]) if soup.select('.lyrics p') else ''
    return {'title': title, 'lyrics': lyrics}
