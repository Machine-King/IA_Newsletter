# db/supabase_client.py: Cliente para interactuar con Supabase PostgreSQL vía REST API.
import os
import requests

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")  # Ej: https://xyzcompany.supabase.co
        self.key = os.getenv("SUPABASE_KEY")  # Clave anon o servicio de Supabase
        if not self.url or not self.key:
            raise ValueError("Faltan variables de entorno SUPABASE_URL o SUPABASE_KEY")
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }

    def insert(self, table: str, data: dict) -> requests.Response:
        """
        Inserta un registro en la tabla especificada de Supabase.
        """
        endpoint = f"{self.url}/rest/v1/{table}"
        try:
            response = requests.post(endpoint, json=data, headers=self.headers)
            return response
        except Exception as e:
            print(f"Error al conectar con Supabase: {e}")
            raise

    def get_all(self, table: str) -> requests.Response:
        """
        Obtiene todos los registros de la tabla especificada de Supabase.
        """
        endpoint = f"{self.url}/rest/v1/{table}?select=*"
        try:
            response = requests.get(endpoint, headers=self.headers)
            return response
        except Exception as e:
            print(f"Error al conectar con Supabase: {e}")
            raise
