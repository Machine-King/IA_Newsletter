# scraper/arxiv_scraper.py: Módulo para obtener los últimos papers de arXiv sobre IA.
import sys
import os
# Agregar el directorio padre al path para permitir importaciones relativas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser
from agent.summarizer import summarize, Deps as SummarizerDeps
from agent.classifier import classify, Deps as ClassifierDeps
from db.supabase_client import SupabaseClient
from dataclasses import dataclass
from httpx import AsyncClient
from dotenv import load_dotenv
import asyncio
import logfire
import ssl

# Configurar SSL para ignorar verificación de certificados (solo para desarrollo)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

load_dotenv()
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()

@dataclass
class Deps:
    client: AsyncClient

async def scrape_arxiv(ctx: Deps):
    """
    Busca los últimos papers en arXiv de la categoría cs.AI y los procesa.
    """
    client = SupabaseClient()
    
    # Usar HTTPS en lugar de HTTP para evitar redirects
    base_url = 'https://export.arxiv.org/api/query?'
    search_query = 'cat:cs.AI'  # Volver a la categoría original que debería funcionar
    max_results = 3  # Reducir para testing y respeto del rate limit
    query = f'search_query={search_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending'
    
    # Construir URL completa
    full_url = base_url + query
    print(f"Consultando URL: {full_url}")
    
    try:
        # Hacer petición HTTP directa con httpx
        response = await ctx.client.get(full_url)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            # Parsear usando feedparser con el contenido obtenido
            feed = feedparser.parse(response.text)
            print(f"Encontrados {len(feed.entries)} papers de arXiv")
        else:
            print(f"Error en la petición HTTP: {response.status_code}")
            # Fallback a feedparser directo
            feed = feedparser.parse(full_url)
            print(f"Fallback feedparser: {len(feed.entries)} papers")
            
    except Exception as e:
        print(f"Error al hacer petición: {e}")
        # Fallback a feedparser directo
        print("Probando con feedparser directo...")
        feed = feedparser.parse(full_url)
        print(f"Con feedparser directo: {len(feed.entries)} papers")
    
    print(f"Encontrados {len(feed.entries)} papers de arXiv")
    
    # Crear contextos para summarizer y classifier
    summarizer_ctx = SummarizerDeps(client=ctx.client)
    classifier_ctx = ClassifierDeps(client=ctx.client)
    
    # Iterar sobre las entradas del feed
    for entry in feed.entries:
        title = entry.get('title', 'Sin título')
        summary_text = entry.get('summary', 'Nada que resumir')  
        link = entry.get('link', 'No link available')
        print(title)
        print(link)
        print(summary_text[:50]) # type: ignore
        print(f"Procesando: {title[:50]}...") # type: ignore
        
        # Llamar al agente para resumir y clasificar
        summary = await summarize(summary_text, summarizer_ctx) # type: ignore
        category = await classify(summary_text, classifier_ctx) # type: ignore
        data = {
            "source": "arXiv",
            "title": title,
            "summary": summary,
            "category": category,
            "url": link
        }
        
        # Insertar en Supabase
        res = client.insert("articles", data)
        if res.status_code != 201:
            print(f"Error al insertar en Supabase: {res.text}")
        else:
            print(f"✓ Insertado correctamente: {title[:30]}...") # type: ignore
        
        # Delay para respetar rate limits de la API
        await asyncio.sleep(5)  # 5 segundos entre requests
    
    return f'Procesados {len(feed.entries)} papers de arXiv'

async def main():
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        result = await scrape_arxiv(ctx=deps)
        print(result)

if __name__ == "__main__":
    print("Iniciando scraper de arXiv...")
    asyncio.run(main())
