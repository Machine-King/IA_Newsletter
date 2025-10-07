from dotenv import load_dotenv
from pydantic_ai import Agent
from shared_definitions import Deps

# Configurar clave de API de Gemini
load_dotenv()
    
async def summarize(text: str, ctx: Deps) -> str:
    """
    Usa el modelo Gemmini para generar un resumen de 2-3 frases del texto dado.
    """
    if not text:
        return ""
    prompt = (
        "Resume el siguiente texto en 5 o 6 frases relevantes:\n\n"
        f"{text}\n\n"
        "***Importante: En caso de recibir un titular, generar descripión extensa.***\n"
        "***Importante: Devulve el resumen sin comentarios adiconales.***\n"
        "Resumen:"
    )

    try:
        agente = Agent('google-gla:gemini-2.5-flash-lite')
        result = await agente.run(prompt, deps=ctx)  # type: ignore
        # Usar try-except para manejar diferentes versiones de la API
        try:
            return result.output
        except AttributeError:
            return f'Error: No output attribute {str(result)}'
    except Exception as e:
        print(f"Error en summarizer: {e}")
        return text[:200] + "..." if len(text) > 200 else text