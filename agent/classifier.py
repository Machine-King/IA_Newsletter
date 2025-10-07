# agent/classifier.py: Llama al API de Gemini (OpenAI) para clasificar el contenido.
from dotenv import load_dotenv
from pydantic_ai import Agent #, RunContext
from shared_definitions import Deps

# Configurar clave de API de Gemini (OpenAI)
load_dotenv()


CATEGORIES = ["investigación", "nuevo_producto", "política/regulación", "opinión/ética", "evento/anuncio"]

async def classify(text: str, ctx: Deps) -> str:
    """
    Usa el modelo Gemini para clasificar el texto en una categoría predefinida.
    """
    if not text:
        return ""
    
    prompt = (
        "Clasifica el siguiente texto en una de las categorías: "
        f"{', '.join(CATEGORIES)}.\n\nTexto:\n{text}\n\n"
        "***Importante: Solo responde con el nombre exacto de la categoría sin explicaciones ni comillas.***\n"
        "Categoría:"
    )
    try:
        agente = Agent('google-gla:gemini-2.5-flash-lite')
        result = await agente.run(prompt)
        # Usar try-except para manejar diferentes versiones de la API
        try:
            return result.output
        except AttributeError:
            return str(result)
    except Exception as e:
        print(f"Error en classifier: {e}")
        return CATEGORIES[0]  # Devolver primera categoría como fallback
