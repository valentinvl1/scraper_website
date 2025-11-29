import subprocess
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

def scrape_all():
    for url in urls:
        print(f"Scraping {url}...")
        try:
            # Run par_scrape using uv
            # We use --output-format markdown to get the text content
            # We use --scraper playwright as default, or we can let it pick default
            cmd = ["uv", "run", "par_scrape", "--url", url, "--output-format", "md", "--run-name", "scraped_sites", "--silent"]
            subprocess.run(cmd, check=True)
            print(f"Successfully scraped {url}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to scrape {url}: {e}")
        
        # Optional: sleep to avoid overwhelming
        time.sleep(2)

if __name__ == "__main__":
    scrape_all()
