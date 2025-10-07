from dataclasses import dataclass
from httpx import AsyncClient
from db.supabase_client import SupabaseClient
from supabase import create_client, Client
import os

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),  # type: ignore
    os.getenv("SUPABASE_KEY")  # type: ignore
    )

@dataclass
class Deps:
    client: AsyncClient

def check_same_articles(source: str, title: str) -> bool:
    client = SupabaseClient()
    try:
        response = supabase.table("articles").select('id').eq("source", source).eq("title", title).execute()
        return len(getattr(response, 'data', [])) > 0
    except Exception as e:
        print(f"Error al verificar artículos similares para {source} y título {title}: {e}")
        return False
    
def upload_data(data: dict) -> bool:
    """
    Sube un artículo a la base de datos si no existe ya un artículo con el mismo título y fuente.
    """
    client = SupabaseClient()
    source = data.get("source", "")
    title = data.get("title", "")
    
    if check_same_articles(source, title):
        print(f"Artículo ya existe en la base de datos: {title}")
        return False
    
    try:
        res_db = client.insert("articles", data)
        if res_db.status_code != 201:
            print(f"Error al insertar artículo en Supabase: {res_db.text}")
            return False
        else:
            print(f"Artículo insertado: {title}")
            return True
    except Exception as e:
        print(f"Error al subir artículo a Supabase: {e}")
        return False