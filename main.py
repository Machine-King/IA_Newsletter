# main.py

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
from scraper.news_scraper import scrape_news
from scraper.arxiv_scraper import scrape_arxiv
from scraper.youtube_scraper import scrape_youtube
import logfire
from dotenv import load_dotenv
import asyncio
import uvicorn
from httpx import AsyncClient
from datetime import date
from shared_definitions import Deps

load_dotenv()

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()



app = FastAPI(title="AI News Summarizer")
templates = Jinja2Templates(directory="templates")

# Configurar archivos estáticos
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# Configurar favicon
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("public/favicon.ico")

# Configurar cliente de Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),  # type: ignore
    os.getenv("SUPABASE_KEY")  # type: ignore
    )

def check_articles_exist_today(source: str) -> bool:
    """
    Verifica si ya existen artículos de una fuente específica para la fecha actual.
    """
    today = str(date.today())
    try:
        response = supabase.table("articles").select('id').eq("date", today).eq("source", source).execute()
        return len(getattr(response, 'data', [])) > 0
    except Exception as e:
        print(f"Error al verificar artículos existentes para {source}: {e}")
        return False

    
@app.get("/")
async def home(request: Request):
    """
    Ruta principal que obtiene los artículos procesados desde Supabase
    y los muestra en la plantilla HTML 'index.html'.
    """
    try:
        # Seleccionamos todas las entradas de la tabla 'articles' ordenadas por fecha (desc) y fuente (asc)
        response = supabase.table("articles").select("*").order("date", desc=True).order("source", desc=False).execute()
        # El cliente de Supabase devuelve los datos en response.data
        articles = getattr(response, 'data', [])
        print(f"Artículos encontrados: {len(articles)}")
    except Exception as e:
        articles = []
        print(f"Error al recuperar datos de Supabase: {e}")
    return templates.TemplateResponse("index.html", {"request": request, "articles": articles})

@app.post("/update/news")
async def update_news():
    """
    Endpoint para actualizar la base de datos con nuevas noticias de TechCrunch y The Verge.
    """
    # Verificar si ya existen noticias para hoy
    if check_articles_exist_today("TheVerge"):
        return JSONResponse(
            content={"message": "Ya existen noticias para la fecha actual", "source": "news", "updated": False}, 
            status_code=201
        )
    
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        try:
            added = await scrape_news(deps)
            return JSONResponse(content={"message": f"Se han añadido {added} noticias", "source": "news", "updated": True}, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar noticias: {str(e)}")

@app.post("/update/arxiv")
async def update_arxiv():
    """
    Endpoint para actualizar la base de datos con nuevos papers de arXiv.
    """
    # Verificar si ya existen papers de arXiv para hoy
    if check_articles_exist_today("arXiv"):
        return JSONResponse(
            content={"message": "Ya existen papers de arXiv para la fecha actual", "source": "arxiv", "updated": False}, 
            status_code=201
        )
    
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        try:
            added = await scrape_arxiv(deps)
            if added == 0:
                return JSONResponse(content={"message": "No se ha encontrado nuevos papers a insertar", "source": "arxiv", "updated": False}, status_code=201)
            return JSONResponse(content={"message": f"Se han añadido {added} papers de arXiv", "source": "arxiv", "updated": True}, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar papers de arXiv: {str(e)}")

@app.post("/update/youtube")
async def update_youtube():
    """
    Endpoint para actualizar la base de datos con nuevos videos de YouTube.
    """
    # Verificar si ya existen videos de YouTube para hoy
    if check_articles_exist_today("YouTube"):
        return JSONResponse(
            content={"message": "Ya existen videos de YouTube para la fecha actual", "source": "youtube", "updated": False}, 
            status_code=201
        )
    
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        try:
            added = await scrape_youtube(deps)
            if added == 0:
                return JSONResponse(content={"message": "No se ha encontrado nuevos videos a insertar", "source": "youtube", "updated": False}, status_code=201)
            return JSONResponse(content={"message": f"Se han añadido {added} videos de YouTube", "source": "youtube", "updated": True}, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar videos de YouTube: {str(e)}")

@app.post("/update/all")
async def update_all():
    """
    Endpoint para actualizar la base de datos con contenido de todas las fuentes.
    Ejecuta todos los scrapers de forma paralela para mejorar el rendimiento.
    """
    # Verificar qué fuentes necesitan actualización
    news_exists = check_articles_exist_today("TheVerge")
    arxiv_exists = check_articles_exist_today("arXiv")
    youtube_exists = check_articles_exist_today("YouTube")
    
    sources_to_update = []
    skipped_sources = []

    if news_exists:
        skipped_sources.append("news")
    else:
        sources_to_update.append("news")
        
    if arxiv_exists:
        skipped_sources.append("arxiv")
    else:
        sources_to_update.append("arxiv")
        
    if youtube_exists:
        skipped_sources.append("youtube")
    else:
        sources_to_update.append("youtube")
    
    # Si todas las fuentes ya están actualizadas
    if not sources_to_update:
        return JSONResponse(
            content={
                "message": "Todas las fuentes ya están actualizadas para la fecha actual",
                "skipped_sources": skipped_sources,
                "updated_sources": [],
                "updated": False
            },
            status_code=201
        )
    
    # Actualizar solo las fuentes que lo necesitan
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        try:
            tasks = []
            deps = Deps(client=client)       
            if "news" in sources_to_update:
                tasks.append(scrape_news(deps))
                
            if "arxiv" in sources_to_update:
                tasks.append(scrape_arxiv(deps))
                
            if "youtube" in sources_to_update:
                tasks.append(scrape_youtube(deps))

            # Ejecutar tareas en paralelo
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            return JSONResponse(
                content={
                    "message": f"Actualización completada. Fuentes actualizadas: {sources_to_update}",
                    "updated_sources": sources_to_update,
                    "skipped_sources": skipped_sources,
                    "updated": True
                },
                status_code=200
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar todas las fuentes: {str(e)}")

async def main():
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    asyncio.run(main())
