# scraper/youtube_scraper.py: Módulo para buscar videos de YouTube sobre 'Inteligencia Artificial'.
import sys
import os
# Agregar el directorio padre al path para permitir importaciones relativas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_search import YoutubeSearch
from agent.summarizer import summarize
from agent.classifier import classify
from db.supabase_client import SupabaseClient
from shared_definitions import Deps, upload_data
from httpx import AsyncClient
from dotenv import load_dotenv
from datetime import date
import logfire
import asyncio

load_dotenv()

async def scrape_youtube(ctx: Deps)-> int:
    """
    Busca videos de YouTube con la palabra clave 'Inteligencia Artificial',
    resume su contenido y los clasifica.
    """
    client = SupabaseClient()
    query = "Inteligencia Artificial"
    max_results = 5
    # Realizar búsqueda en YouTube (sin API oficial)
    results = YoutubeSearch(query, max_results=max_results).to_dict()
    print(results)
    añadidos=0
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
        #Get current date
        current_date = str(date.today().isoformat())
        data = {
            "source": "YouTube",
            "title": title,
            "summary": summary,
            "category": category,
            "url": url,
            "date": current_date
        }
        if upload_data(data):
            print(f"✓ Insertado correctamente: {title[:30]}...") # type: ignore
            añadidos += 1
        else:
            print(f"✗ No insertado (posible duplicado): {title[:30]}...") # type: ignore
    return añadidos

async def main():
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        await scrape_youtube(ctx=deps)

if __name__ == "__main__":
    asyncio.run(main())
