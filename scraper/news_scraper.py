# scraper/news_scraper.py: Módulo para obtener noticias de TechCrunch y The Verge sobre IA.
import sys
import os
# Agregar el directorio padre al path para permitir importaciones relativas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser
from agent.summarizer import summarize
from agent.classifier import classify
from db.supabase_client import SupabaseClient
import asyncio
from shared_definitions import Deps, upload_data
from httpx import AsyncClient
from dotenv import load_dotenv
import logfire
from datetime import datetime

load_dotenv()


async def scrape_news(ctx: Deps)-> int:
    """
    Recolecta las últimas noticias de TechCrunch (categoría IA) y The Verge (tema IA),
    y las procesa.
    """
    client = SupabaseClient()
    feeds = {
        "TechCrunch": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "TheVerge": "https://www.theverge.com/rss/index.xml"
    }
    añadidos=0
    for source, feed_url in feeds.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # Tomar hasta 5 entradas por feed
            title = entry.title
            # Dependiendo del feed, la descripción puede llamarse summary o description
            summary_text = entry.summary if 'summary' in entry else entry.get('description', '')
            link = entry.link
            date_str = entry.get('published', 'No date available')
            # Original string
            # Parse the date string to a datetime object
            try:
                dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z") # type: ignore
            except ValueError:
                dt = datetime.fromisoformat(date_str) # type: ignore
            # Convert to ISO 8601 format
            date_str = dt.strftime("%Y-%m-%d")
            # Resumir y clasificar
            summary = await summarize(summary_text, ctx) # type: ignore
            category = await classify(summary_text, ctx) # type: ignore
            data = {
                "source": source,
                "title": title,
                "summary": summary,
                "category": category,
                "url": link,
                "date": date_str,
            }
            if upload_data(data):
                print(f"✓ Insertado correctamente: {title[:30]}...") # type: ignore
                añadidos+=1
            else:
                print(f"✗ No insertado (posible duplicado): {title[:30]}...") # type: ignore
    return añadidos
async def main():
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        await scrape_news(ctx=deps)

if __name__ == "__main__":
    asyncio.run(main())