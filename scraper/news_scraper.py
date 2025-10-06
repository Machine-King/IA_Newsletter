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
from dataclasses import dataclass
from httpx import AsyncClient
from dotenv import load_dotenv
import logfire

load_dotenv()
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()

@dataclass
class Deps:
    client: AsyncClient

async def scrape_news(ctx: Deps):
    """
    Recolecta las últimas noticias de TechCrunch (categoría IA) y The Verge (tema IA),
    y las procesa.
    """
    client = SupabaseClient()
    feeds = {
        "TechCrunch": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "TheVerge": "https://www.theverge.com/rss/index.xml"
    }
    for source, feed_url in feeds.items():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:  # Tomar hasta 5 entradas por feed
            title = entry.title
            # Dependiendo del feed, la descripción puede llamarse summary o description
            summary_text = entry.summary if 'summary' in entry else entry.get('description', '')
            link = entry.link
            # Filtrar si es The Verge: solo incluir noticias que mencionan 'IA' o 'AI'
            if source == "TheVerge":
                text_lower = (title + summary_text).lower() # type: ignore
                if not ("ai" in text_lower or "inteligencia artificial" in text_lower):
                    continue
            # Resumir y clasificar
            summary = await summarize(summary_text, ctx) # type: ignore
            category = await classify(summary_text, ctx) # type: ignore
            data = {
                "source": source,
                "title": title,
                "summary": summary,
                "category": category,
                "url": link
            }
            res_db = client.insert("articles", data)
            if res_db.status_code != 201:
                print(f"Error al insertar noticia en Supabase: {res_db.text}")
            else:
                print(f"Noticia insertada: {title}")

async def main():
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        await scrape_news(ctx=deps)

if __name__ == "__main__":
    asyncio.run(main())