import pandas as pd
import os
import json
import re
import unicodedata
from collections import Counter
from openai import OpenAI
from colorama import Fore, Style, init

init(autoreset=True)

# CONFIGURACIÓN INICIAL
MODELO_JUEZ = "llama-3.2-3b-instruct"
CLIENT = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
ARCHIVO_CSV = "resultados_benchmark.csv"
ARCHIVO_DATASET = "dataset_pruebas.json"


def quitar_acentos(s):
    """
    Elimina los signos diacríticos de una cadena de texto.
    Garantiza que variaciones menores en la respuesta (como omitir una tilde)
    no provoquen un falso negativo durante la validación estricta.
    """
    return ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn')


def cargar_diccionario_problemas():
    """
    Carga el dataset original para extraer los enunciados de los problemas.
    El Juez necesita el contexto original del problema para poder evaluar
    respuestas complejas o ambiguas de manera correcta.
    """
    if not os.path.exists(ARCHIVO_DATASET):
        return {}

    with open(ARCHIVO_DATASET, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    return {f"{item['id_original']}_{item['dificultad'].lower()}_{item['variante'].lower()}": item['problema_texto'] for
            item in datos}


def evaluacion_rapida(esperada, obtenida):
    """
    Filtro heurístico de alta velocidad (Fast-Eval).
    Comprueba casos donde la respuesta del modelo es estructuralmente perfecta o evidente.
    Su función es ahorrar tiempo y tokens evitando llamadas costosas a la API del LLM
    cuando la respuesta ya es claramente un acierto.
    """
    if pd.isna(obtenida) or str(obtenida).strip() == "":
        return False

    esp, obt = quitar_acentos(str(esperada).strip().lower()), quitar_acentos(str(obtenida).strip().lower())

    # Comprueba si el modelo respondió con el formato de barra y el lado izquierdo es perfecto
    partes = [p.strip() for p in obt.split('|')]
    if len(partes) >= 1 and partes[0] == esp:
        return True

    # Comprueba si el modelo devolvió únicamente la respuesta aislada
    if obt == esp:
        return True

    # Comprueba si el modelo usó la palabra clave requerida aunque fallara otras reglas
    match_sol = re.search(r"soluci[oó]n:\s*([^\n|]+)", obt)
    if match_sol and match_sol.group(1).strip() == esp:
        return True

    return None


def juzgar_respuesta_ia(problema_texto, esperada, respuesta_obtenida):
    """
    Delega la decisión al modelo de lenguaje configurado como Juez cuando
    la heurística rápida no puede determinar con seguridad el resultado.

    Técnicas de Prompt Engineering aplicadas en esta función:
    - ROLE-PLAYING: Sitúa al modelo en la figura de un evaluador estricto.
    - EXPLICIT CONSTRAINTS: Se definen fronteras claras sobre lo que debe ignorar (unidades, formato, confianza).
    - FEW-SHOT PROMPTING: Se inyectan ejemplos específicos de casos límite (respuestas ambiguas o con métricas)
      para calibrar la forma en la que el Juez debe interpretar las respuestas de otros modelos.
    """
    prompt_juez = f"""Evalúa si la respuesta final de un modelo de IA es lógicamente correcta basándote en la solución oficial.

REGLAS ESTRICTAS:
1. Compara el significado de la "Respuesta obtenida" con la "Solución esperada".
2. Ignora la palabra "Solución:" inicial, texto adicional menor, y el número de "Confianza" (que suele estar tras la barra '|').
3. Si la respuesta contiene la solución pero incluye otras opciones (ej: "Sí | No"), es SUSPENSO.
4. Responde ÚNICAMENTE con la palabra "APROBADO" (si acertó la respuesta) o "SUSPENSO" (si falló o es ambigua).

--- EJEMPLOS ---
Solución esperada: 0
Respuesta obtenida: 0 | 100
Evaluación: APROBADO

Solución esperada: 10
Respuesta obtenida: Solución: 3 | Confianza: 80
Evaluación: SUSPENSO

Solución esperada: 1
Respuesta obtenida: Saldo: +1 | Confianza: 80
Evaluación: APROBADO

Solución esperada: 10
Respuesta obtenida: Desplazamiento: 36000 metros | Confianza: 100
Evaluación: SUSPENSO

--- CASO A EVALUAR ---
Pregunta original: {problema_texto}
Solución esperada: {esperada}
Respuesta obtenida: {respuesta_obtenida}
Evaluación:"""

    try:
        response = CLIENT.chat.completions.create(
            model=MODELO_JUEZ,
            messages=[{"role": "user", "content": prompt_juez}],
            temperature=0.0,
            max_tokens=10
        )
        veredicto = response.choices[0].message.content.strip().upper()
        return "APROBADO" in veredicto and "SUSPENSO" not in veredicto
    except:
        return False


def juzgar_general(problema_texto, esperada, obtenida):
    """
    Orquesta la evaluación híbrida. Intenta primero el método local rápido
    y solo recurre a la IA si el caso es ambiguo o complejo.
    """
    res_rapido = evaluacion_rapida(esperada, obtenida)
    if res_rapido is not None:
        return res_rapido

    return juzgar_respuesta_ia(problema_texto, esperada, obtenida)


def procesar_csv_con_juez():
    """
    Itera sobre el archivo de resultados principal para auditar las respuestas.
    Añade nuevas columnas con el veredicto del Juez y calcula la tasa de discrepancia.
    Es tolerante a fallos: solo evalúa las filas que aún no han sido juzgadas.
    """
    if not os.path.exists(ARCHIVO_CSV):
        print(f"{Fore.RED}No existe {ARCHIVO_CSV}. Ejecuta el main primero.{Style.RESET_ALL}")
        return

    dicc_problemas = cargar_diccionario_problemas()
    df = pd.read_csv(ARCHIVO_CSV)

    columnas_juez = ['Juez_Rep_1', 'Juez_Rep_2', 'Juez_Rep_3', 'Acierto_Juez_Mayoria', 'Tasa_Acierto_Juez_%',
                     'Discrepancia_Mayoria']

    for col in columnas_juez:
        if col not in df.columns:
            df[col] = pd.NA

    print(f"{Fore.CYAN}Iniciando evaluación HÍBRIDA (Fast-Eval + Juez {MODELO_JUEZ})...{Style.RESET_ALL}")

    modificados = False
    for index, row in df.iterrows():

        if pd.isna(row['Tasa_Acierto_Juez_%']):
            print(f"Juez evaluando fila {index + 1}/{len(df)} (Modelo: {row['Modelo']})...")

            esperada = row['Solucion_Esperada']
            key = f"{row['ID_Problema']}_{str(row['Dificultad']).lower()}_{str(row['Variante']).lower()}"
            problema_texto = dicc_problemas.get(key, "[Texto no disponible]")

            j1 = juzgar_general(problema_texto, esperada, row.get('Rep_1', ''))
            j2 = juzgar_general(problema_texto, esperada, row.get('Rep_2', ''))
            j3 = juzgar_general(problema_texto, esperada, row.get('Rep_3', ''))

            aciertos = [j1, j2, j3]
            acierto_juez = Counter(aciertos).most_common(1)[0][0]

            df.at[index, 'Juez_Rep_1'] = j1
            df.at[index, 'Juez_Rep_2'] = j2
            df.at[index, 'Juez_Rep_3'] = j3
            df.at[index, 'Acierto_Juez_Mayoria'] = acierto_juez
            df.at[index, 'Tasa_Acierto_Juez_%'] = (sum(aciertos) / 3) * 100

            # Cálculo de Discrepancia: Permite detectar modelos con alta capacidad lógica
            # pero baja obediencia a las reglas de formato estipuladas.
            df.at[index, 'Discrepancia_Mayoria'] = (row['Acierto_Mayoria'] == False and acierto_juez == True)

            modificados = True

    if modificados:
        df.to_csv(ARCHIVO_CSV, index=False)
        print(f"{Fore.GREEN}¡Evaluación finalizada! Guardado en {ARCHIVO_CSV}.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Todo estaba ya evaluado por el juez. No se ha modificado el archivo.{Style.RESET_ALL}")


if __name__ == "__main__":
    input(f"{Fore.YELLOW}Asegúrate de cargar '{MODELO_JUEZ}' en LM Studio y presiona ENTER...{Style.RESET_ALL}")
    procesar_csv_con_juez()