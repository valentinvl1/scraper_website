import os
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

urls = [
  "https://www.axeptio.eu",
  "https://opt-out.ferank.eu/fr/install/",
  "https://www.didomi.io",
  "https://www.lemonde.fr",
  "https://www.lefigaro.fr",
  "https://www.liberation.fr",
  "https://www.20minutes.fr",
  "https://www.carrefour.fr",
  "https://www.fnac.com",
  "https://www.cdiscount.com",
  "https://www.laredoute.fr",
  "https://www.service-public.fr",
  "https://www.ameli.fr",
  "https://www.impots.gouv.fr",
  "https://www.bnpparibas.com",
  "https://www.creditagricole.fr",
  "https://www.labanquepostale.fr",
  "https://www.cookielaw.org/demo",
  "https://www.trustarc.com",
  "https://www.iubenda.com",
  "https://www.onetrust.com",
  "https://www.bbc.com",
  "https://www.cnn.com",
  "https://www.theguardian.com"
]

output_dir = "scraped_data"
os.makedirs(output_dir, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_filename(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/").replace("/", "_")
    if path:
        return f"{domain}_{path}.txt"
    return f"{domain}.txt"

def scrape_url(url):
    try:
        print(f"Scraping {url}...")
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text(separator='\n', strip=True)
        
        filename = get_filename(url)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n\n")
            f.write(text)
            
        print(f"Saved to {filepath}")
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")

def main():
    for url in urls:
        scrape_url(url)
        time.sleep(1) # Be polite

if __name__ == "__main__":
    main()
