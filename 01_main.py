import json
import time
import os
import re
import unicodedata
import pandas as pd
from collections import Counter
from openai import OpenAI
from colorama import Fore, Style, init

init(autoreset=True)

# Configuración base para la conexión con la API local de LM Studio
API_URL = "http://localhost:1234/v1"
API_KEY = "lm-studio"

REPETICIONES_POR_PROMPT = 3 # Define el número de veces que se enviará el mismo prompt al modelo para calcular moda y consistencia
ARCHIVO_RESULTADOS = "resultados_benchmark.csv"

# Lista de los modelos que hemos instalado y probado en LM Studio
MODELOS_DISPONIBLES = [
    "llama-3.2-3b-instruct",
    "tinyllama-1.1b-chat",
    "ministral-3-3b",
    "lfm2.5-1.2b",
    "qwen2.5-3b-instruct"
]

client = OpenAI(base_url=API_URL, api_key=API_KEY)


def quitar_acentos(s):
    """
    Elimina los signos diacríticos (tildes) de una cadena de texto.
    Se utiliza para evitar que diferencias menores de ortografía (ej: miércoles vs miercoles)
    sean marcadas como errores durante la validación estricta.
    """
    return ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn')


def parsear_respuesta(texto_crudo):
    """
    Extrae la solución lógica y el nivel de confianza reportado por el modelo a partir del texto bruto.
    Busca patrones de texto exactos ignorando mayúsculas y minúsculas.
    """
    solucion = ""
    confianza = 0

    # La extracción se detiene si encuentra un salto de línea o el carácter separador '|'
    match_sol = re.search(r"Soluci[oó]n:\s*([^\n|]+)", texto_crudo, re.IGNORECASE)
    match_conf = re.search(r"Confianza:\s*(\d+)", texto_crudo, re.IGNORECASE)

    if match_sol:
        solucion = match_sol.group(1).strip().lower()
    if match_conf:
        try:
            confianza = int(match_conf.group(1))
        except ValueError:
            confianza = 0

    return solucion, confianza


def consulta_unica(prompt, modelo_id):
    """
    Envía un único prompt al modelo de lenguaje a través de la API y mide el tiempo de respuesta
    y el consumo de tokens.
    """
    start_time = time.time()

    # Técnicas de Prompt Engineering utilizadas para guiar al modelo:
    # ROL: Se le asigna una identidad específica ("sistema de evaluación lógico").
    # CONSTRAINTS: Límites estrictos de longitud (dos líneas) y de formato (sin markdown).
    # EXPLICIT FORMATTING: Se le obliga a usar claves concretas ("Solución:" y "Confianza:").
    # FEW-SHOT PROMPTING: Se le proporcionan interacciones resueltas para que imite la estructura.
    system_prompt = """Eres un sistema de evaluación lógico y matemático. Tu respuesta debe ser SOLO DOS LÍNEAS, sin formato markdown ni texto extra.
Sigue EXACTAMENTE este formato estricto:
Solución: [tu respuesta final, una sola palabra o número]
Confianza: [tu nivel de seguridad del 0 al 100]

--- EJEMPLO 1 ---
Usuario: ¿Cuánto es la mitad de 10?
Asistente:
Solución: 5
Confianza: 100

--- EJEMPLO 2 ---
Usuario: Si ayer fue martes, ¿qué día es hoy?
Asistente:
Solución: miércoles
Confianza: 95
"""

    try:
        response = client.chat.completions.create(
            model=modelo_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )
        duration = time.time() - start_time
        texto_crudo = response.choices[0].message.content.strip()
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens

        solucion, confianza = parsear_respuesta(texto_crudo)
        return solucion, confianza, tokens_in, tokens_out, duration, texto_crudo
    except Exception as e:
        print(f"{Fore.RED}Error en API de LM Studio: {e}{Style.RESET_ALL}")
        return "", 0, 0, 0, 0.0, ""


def evaluar_con_repeticiones(prompt, esperada, modelo_id, repeticiones):
    """
    Envía el mismo prompt de forma repetida para evaluar la consistencia de las respuestas
    y calcula las métricas promediadas de rendimiento (tokens, tiempo, confianza).
    """
    aciertos_estrictos, confianzas, tiempos, respuestas_crudas = [], [], [], []
    t_in, t_out = 0, 0
    esperada_limpia = quitar_acentos(esperada).lower()

    for _ in range(repeticiones):
        sol, conf, in_tok, out_tok, dur, texto_crudo = consulta_unica(prompt, modelo_id)

        # Validación estricta: se comprueba tanto que haya seguido el formato requerido
        # como que el valor extraído coincida exactamente con la solución esperada.
        if sol != "":
            sol_limpia = quitar_acentos(sol)
            coincidencia = (sol_limpia == esperada_limpia)
        else:
            # Fallo automático por no respetar las reglas de formato del prompt
            coincidencia = False

        aciertos_estrictos.append(coincidencia)
        confianzas.append(conf)
        respuestas_crudas.append(texto_crudo)

        t_in += in_tok
        t_out += out_tok
        tiempos.append(dur)

    conteo = Counter(aciertos_estrictos)
    tiempo_medio = sum(tiempos) / repeticiones
    avg_t_out = t_out / repeticiones

    resultado = {
        "Acierto_Mayoria": conteo.most_common(1)[0][0],
        "Tasa_Acierto_%": round((sum(aciertos_estrictos) / repeticiones) * 100, 2),
        "Confianza_Media_%": round(sum(confianzas) / repeticiones if repeticiones > 0 else 0, 2),
        "Tokens_Prompt": round(t_in / repeticiones),
        "Tokens_Respuesta": round(avg_t_out),
        "Tiempo_Medio_s": round(tiempo_medio, 2),
        "Tokens_por_Segundo": round(avg_t_out / tiempo_medio if tiempo_medio > 0 else 0, 2)
    }

    # Se guarda el output bruto del modelo para poder auditarlo a posteriori
    for i, resp in enumerate(respuestas_crudas):
        resultado[f"Rep_{i + 1}"] = resp.replace("\n", " | ")

    return resultado


def mostrar_menu_y_seleccionar(total_prompts):
    """
    Muestra la interfaz de usuario por consola para seleccionar qué modelo evaluar.
    Indica el progreso actual basándose en los registros existentes en el archivo CSV.
    """
    df_existente = None
    conteo_modelos = {}

    if os.path.exists(ARCHIVO_RESULTADOS):
        df_existente = pd.read_csv(ARCHIVO_RESULTADOS)
        conteo_modelos = df_existente['Modelo'].value_counts().to_dict()

    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f" MENÚ DE SELECCIÓN DE MODELOS (Prompts totales: {total_prompts})")
    print(f"{'=' * 60}{Style.RESET_ALL}")

    for i, modelo in enumerate(MODELOS_DISPONIBLES, 1):
        count = conteo_modelos.get(modelo, 0)
        estado = f"{Fore.GREEN}Completado ({count}/{total_prompts}){Style.RESET_ALL}" if count >= total_prompts else \
            f"{Fore.YELLOW}Incompleto ({count}/{total_prompts}){Style.RESET_ALL}" if count > 0 else \
                f"{Fore.RED}Pendiente (0/{total_prompts}){Style.RESET_ALL}"
        print(f" {i}. {modelo.ljust(25)} -> {estado}")

    print(f"\n {Fore.CYAN}0. Salir del programa{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

    while True:
        opcion = input("Selecciona un número (0-5): ").strip()
        if opcion == '0': return None, df_existente
        try:
            idx = int(opcion) - 1
            if 0 <= idx < len(MODELOS_DISPONIBLES):
                mod = MODELOS_DISPONIBLES[idx]

                # Si el modelo fue evaluado de forma parcial, se descartan los datos antiguos
                # para forzar una reevaluación limpia desde cero.
                if df_existente is not None and mod in conteo_modelos and 0 < conteo_modelos[mod] < total_prompts:
                    df_existente = df_existente[df_existente['Modelo'] != mod]
                return mod, df_existente
        except ValueError:
            pass
        print(f"{Fore.RED}Entrada no válida. Selecciona un número del menú.{Style.RESET_ALL}")


def ejecutar_benchmark_modelo(modelo, datos, df_existente):
    """
    Controla el flujo de evaluación de un modelo específico iterando sobre
    todo el dataset de pruebas y guardando los resultados incrementales.
    """
    nuevos_resultados = []
    input(f"\n{Fore.YELLOW}⚠️ Carga '{modelo}' en LM Studio y presiona ENTER para comenzar...{Style.RESET_ALL}")

    for index, item in enumerate(datos):
        print(
            f"[{modelo}] Evaluando: {item['id_original']} ({item['categoria']}) | {item['dificultad']} - {item['variante']} | Progreso: {index + 1}/{len(datos)}")

        metricas = evaluar_con_repeticiones(item['problema_texto'], item['solucion_esperada'], modelo,
                                            REPETICIONES_POR_PROMPT)

        fila = {"Modelo": modelo, "ID_Problema": item['id_original'], "Categoria": item['categoria'].capitalize(),
                "Dificultad": item['dificultad'].capitalize(), "Variante": item['variante'].capitalize(),
                "Solucion_Esperada": item['solucion_esperada'],
                "Tokens_Totales": metricas['Tokens_Prompt'] + metricas['Tokens_Respuesta'],
                **metricas}

        nuevos_resultados.append(fila)

    df_nuevos = pd.DataFrame(nuevos_resultados)

    # Se fusionan los nuevos datos con los existentes, priorizando la ejecución más reciente en caso de duplicados
    if df_existente is not None and not df_existente.empty:
        df_final = pd.concat([df_existente, df_nuevos], ignore_index=True)
        df_final.drop_duplicates(subset=['Modelo', 'ID_Problema', 'Dificultad', 'Variante'], keep='last', inplace=True)
    else:
        df_final = df_nuevos

    df_final.to_csv(ARCHIVO_RESULTADOS, index=False, encoding='utf-8')
    print(f"\n{Fore.GREEN}¡Evaluación de {modelo} completada y datos guardados!{Style.RESET_ALL}")


if __name__ == "__main__":
    if not os.path.exists("dataset_pruebas.json"):
        print(
            f"{Fore.RED}Error: El archivo fuente de prompts no existe. Ejecuta primero generador_prompts.py{Style.RESET_ALL}")
        exit()

    with open("dataset_pruebas.json", 'r', encoding='utf-8') as f:
        datos = json.load(f)
    total_prompts = len(datos)

    while True:
        modelo_seleccionado, df_estado = mostrar_menu_y_seleccionar(total_prompts)
        if modelo_seleccionado is None:
            print(
                f"\n{Fore.GREEN}Proceso finalizado.{Style.RESET_ALL}")
            break
        ejecutar_benchmark_modelo(modelo_seleccionado, datos, df_estado)