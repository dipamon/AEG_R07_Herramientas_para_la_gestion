import time
import math
import numpy as np
from openai import OpenAI
from colorama import Fore, Style, init

# Inicializar colores para la terminal
init(autoreset=True)

# CONFIGURACIÓN
# Asegúrate de que el servidor de LM Studio esté corriendo en el puerto 1234
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")


def calcular_metricas(logprobs_content):
    """
    Calcula métricas avanzadas basadas en los logprobs de cada token.
    """
    if not logprobs_content:
        return 0.0, 0.0

    # Extraemos los valores de logprob de la lista de tokens
    probs = [token.logprob for token in logprobs_content]

    # 1. Confianza Promedio (Average Confidence)
    # Convertimos logaritmos a probabilidad lineal (0 a 100%)
    linear_probs = [math.exp(p) for p in probs]
    avg_confidence = np.mean(linear_probs) * 100

    # 2. Perplejidad (Perplexity)
    # Medida de "sorpresa". Menor es mejor (más predecible/seguro).
    # Perplejidad = exp(-1 * media(logprobs))
    avg_logprob = np.mean(probs)
    perplexity = math.exp(-1 * avg_logprob)

    return avg_confidence, perplexity


def probar_modelo(prompt, modelo_id="local-model"):
    print(f"{Fore.CYAN}--- Enviando Prompt... ---{Style.RESET_ALL}")

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model=modelo_id,
            messages=[
                {"role": "system", "content": "Eres un asistente útil y preciso."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            logprobs=True,  # IMPRESCINDIBLE: Pedimos los datos "geek"
            top_logprobs=1
        )

        end_time = time.time()
        duration = end_time - start_time

        # Extracción de datos básica
        mensaje = response.choices[0].message.content
        tokens_input = response.usage.prompt_tokens
        tokens_output = response.usage.completion_tokens
        finish_reason = response.choices[0].finish_reason

        # --- EXTRACCIÓN SEGURA DE LOGPROBS ---
        # Verificamos que logprobs exista y no sea None antes de pedir su content
        if getattr(response.choices[0], "logprobs", None) is not None:
            logprobs_data = response.choices[0].logprobs.content
        else:
            logprobs_data = None
            print(f"{Fore.YELLOW}⚠️ Aviso: LM Studio no devolvió datos de logprobs.{Style.RESET_ALL}")

        # Calcular nuestras métricas personalizadas
        confianza, perplejidad = calcular_metricas(logprobs_data)

        # Calcular nuestras métricas personalizadas
        confianza, perplejidad = calcular_metricas(logprobs_data)

        # Métrica combinada de Rendimiento (Tokens por Segundo)
        tps = tokens_output / duration if duration > 0 else 0

        # --- REPORTE EN CONSOLA ---
        print(f"\n{Fore.GREEN}Respuesta del Modelo:{Style.RESET_ALL}")
        print(mensaje)
        print(f"\n{Fore.YELLOW}--- GEEK DATA (Métricas) ---{Style.RESET_ALL}")
        print(f"⏱️  Tiempo Total:      {duration:.2f} s")
        print(f"🚀 Velocidad:         {tps:.2f} tokens/s")
        print(f"🧠 Confianza Modelo:  {confianza:.2f}% (Seguridad interna)")
        print(f"🤔 Perplejidad:       {perplejidad:.2f} (Menos es mejor)")
        print(f"🛑 Motivo de parada:  {finish_reason}")
        print(f"💰 Tokens (In/Out):   {tokens_input} / {tokens_output}")
        print("-" * 50)

        return {
            "prompt": prompt,
            "respuesta": mensaje,
            "confianza": confianza,
            "perplejidad": perplejidad,
            "tiempo": duration
        }

    except Exception as e:
        print(f"{Fore.RED}Error conectando con LM Studio: {e}{Style.RESET_ALL}")
        return None


# --- ZONA DE PRUEBAS ---
if __name__ == "__main__":
    # Define aquí el ID exacto del modelo cargado en LM Studio o usa "local-model"
    # si solo tienes uno cargado.
    MODEL_ID = "local-model"

    mi_prompt = "Explica en un párrafo corto por qué el cielo es azul. Al final, devuelve la confianza con la que das la respuesta 'CONF: X%'"

    probar_modelo(mi_prompt, MODEL_ID)