import requests
from bs4 import BeautifulSoup

TRUNCATE_SCRAPED_TEXT = 50000
def retrieve_content(url, max_tokens=TRUNCATE_SCRAPED_TEXT):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        text = soup.get_text(separator=' ', strip=True)
        characters = max_tokens * 4
        text = text[:characters]
        return text
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return None