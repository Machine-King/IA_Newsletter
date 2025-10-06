# main.py

import os
import jinja2
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
from scraper.news_scraper import scrape_news
from scraper.arxiv_scraper import scrape_arxiv
from scraper.youtube_scraper import scrape_youtube
import logfire
from dotenv import load_dotenv
import asyncio
import concurrent.futures
import uvicorn
from dataclasses import dataclass
from httpx import AsyncClient

load_dotenv()

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()

@dataclass
class Deps:
    client: AsyncClient

app = FastAPI(title="AI News Summarizer")
templates = Jinja2Templates(directory="templates")

# Configurar archivos estáticos
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
# Configurar cliente de Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),  # type: ignore
    os.getenv("SUPABASE_KEY")  # type: ignore
    )

@app.get("/")
async def home(request: Request):
    """
    Ruta principal que obtiene los artículos procesados desde Supabase
    y los muestra en la plantilla HTML 'index.html'.
    """
    try:
        # Seleccionamos todas las entradas de la tabla 'articles'
        response = supabase.table("articles").select("*").execute()
        # El cliente de Supabase devuelve los datos en response.data
        articles = getattr(response, 'data', []) or []
        print(f"Artículos encontrados: {len(articles)}")
        print(articles)
    except Exception as e:
        articles = []
        print(f"Error al recuperar datos de Supabase: {e}")
    return templates.TemplateResponse("index.html", {"request": request, "articles": articles})

@app.post("/update/news")
async def update_news():
    """
    Endpoint para actualizar la base de datos con nuevas noticias de TechCrunch y The Verge.
    """
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        try:
            await asyncio.to_thread(scrape_news, deps) # type: ignore
            return JSONResponse(content={"message": "Noticias actualizadas correctamente", "source": "news"}, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar noticias: {str(e)}")

@app.post("/update/arxiv")
async def update_arxiv():
    """
    Endpoint para actualizar la base de datos con nuevos papers de arXiv.
    """
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        try:
            await asyncio.to_thread(scrape_arxiv, deps) # type: ignore
            return JSONResponse(content={"message": "Papers de arXiv actualizados correctamente", "source": "arxiv"}, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar papers de arXiv: {str(e)}")

@app.post("/update/youtube")
async def update_youtube():
    """
    Endpoint para actualizar la base de datos con nuevos videos de YouTube.
    """
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        try:
            await asyncio.to_thread(scrape_youtube, deps) # type: ignore
            return JSONResponse(content={"message": "Videos de YouTube actualizados correctamente", "source": "youtube"}, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar videos de YouTube: {str(e)}")

@app.post("/update/all")
async def update_all():
    """
    Endpoint para actualizar la base de datos con contenido de todas las fuentes.
    Ejecuta todos los scrapers de forma paralela para mejorar el rendimiento.
    """
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        try:
            # Ejecutar todos los scrapers en paralelo usando ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Crear futures para cada scraper
                def run_scraper(scraper_func, deps):
                    scraper_func(deps)
                    return None

                news_future = executor.submit(run_scraper, scrape_news, deps)
                arxiv_future = executor.submit(run_scraper, scrape_arxiv, deps)
                youtube_future = executor.submit(run_scraper, scrape_youtube, deps)

                # Esperar a que todos terminen
                concurrent.futures.wait([news_future, arxiv_future, youtube_future])
                
                # Verificar si alguno falló
                results = []
                if news_future.exception():
                    results.append(f"Error en news: {news_future.exception()}")
                else:
                    results.append("Noticias actualizadas")
                    
                if arxiv_future.exception():
                    results.append(f"Error en arXiv: {arxiv_future.exception()}")
                else:
                    results.append("Papers de arXiv actualizados")
                    
                if youtube_future.exception():
                    results.append(f"Error en YouTube: {youtube_future.exception()}")
                else:
                    results.append("Videos de YouTube actualizados")
            
            return JSONResponse(content={
                "message": "Actualización completa finalizada",
                "results": results,
                "sources": ["news", "arxiv", "youtube"]
            }, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar todas las fuentes: {str(e)}")

async def main():
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    asyncio.run(main())
