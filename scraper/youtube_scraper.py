# scraper/youtube_scraper.py: Módulo para buscar videos de YouTube sobre 'Inteligencia Artificial'.
import sys
import os
# Agregar el directorio padre al path para permitir importaciones relativas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_search import YoutubeSearch
from agent.summarizer import summarize
from agent.classifier import classify
from db.supabase_client import SupabaseClient
from dataclasses import dataclass
from httpx import AsyncClient
from dotenv import load_dotenv
import logfire
import asyncio

load_dotenv()
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()

@dataclass
class Deps:
    client: AsyncClient

async def scrape_youtube(ctx: Deps):
    """
    Busca videos de YouTube con la palabra clave 'Inteligencia Artificial',
    resume su contenido y los clasifica.
    """
    client = SupabaseClient()
    query = "Inteligencia Artificial"
    max_results = 3
    # Realizar búsqueda en YouTube (sin API oficial)
    results = YoutubeSearch(query, max_results=max_results).to_dict()
    print(results)
    for res in results:
        title = res.get('title', 'Sin título') # type: ignore
        # Construir URL completo del video
        url = f"https://www.youtube.com{res.get('url_suffix', '')}" # type: ignore
        # Tomar la descripción o canal como texto base (si está disponible)
        snippet = res.get('long_desc', '') or title # type: ignore
        text_to_summarize = snippet if snippet else title
        print('Texto a resumir:', text_to_summarize)
        summary = await summarize(text_to_summarize, ctx) # type: ignore
        print(f"Resumen generado: {summary}")
        category = await classify(text_to_summarize, ctx) # type: ignore
        data = {
            "source": "YouTube",
            "title": title,
            "summary": summary,
            "category": category,
            "url": url
        }
        res_db = client.insert("articles", data)
        if res_db.status_code != 201:
            print(f"Error al insertar video en Supabase: {res_db.text}")
        else:
            print(f"Video insertado: {title}")

async def main():
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        await scrape_youtube(ctx=deps)

if __name__ == "__main__":
    asyncio.run(main())
