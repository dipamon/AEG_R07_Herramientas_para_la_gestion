import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from colorama import Fore, Style, init

init(autoreset=True)

# ASIGNACIÓN DE COLORES
# Definición de paletas estáticas para garantizar la coherencia visual en todo el panel.
# Un modelo o variante mantendrá exactamente el mismo color en cualquier gráfico generado.

PALETA_MODELOS = {
    "llama-3.2-3b-instruct": "#81ecec",
    "tinyllama-1.1b-chat": "#636e72",
    "ministral-3-3b": "#4a69bd",
    "lfm2.5-1.2b": "#a29bfe",
    "qwen2.5-3b-instruct": "#fdcb6e"
}

PALETA_VARIANTES = {
    "Original": "#b2bec3",
    "Duplicado": "#74b9ff",
    "Repito": "#55efc4",
    "Frase": "#ff7675"
}

PALETA_CATEGORIAS = {
    "Matematico": "#74b9ff",
    "Logico": "#fab1a0"
}

ORDEN_VARIANTES = ["Original", "Duplicado", "Repito", "Frase"]


# CONFIGURACIÓN VISUAL GLOBAL
def configurar_estilo():
    """
    Aplica un tema global de Seaborn orientado a presentaciones (context="talk").
    Ajusta proporcionalmente los tamaños de fuente, aplica negritas a los ejes
    y asegura una resolución de guardado óptima para documentos profesionales.
    """
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update({
        'figure.figsize': (14, 8),
        'axes.titlesize': 20,
        'axes.titleweight': 'bold',
        'axes.titlepad': 20,
        'axes.labelsize': 14,
        'axes.labelweight': 'bold',
        'axes.labelpad': 12,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'legend.title_fontsize': 14,
        'savefig.dpi': 300
    })


def estilizar_leyenda():
    """
    Formatea la leyenda del gráfico activo.
    Identifica los subtítulos internos para resaltarlos en negrita e inyecta
    espaciado vertical estratégico para evitar que los bloques de categorías se solapen.
    """
    leg = plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', labelspacing=1.2, borderpad=1)
    if leg is None:
        return
    for text in leg.texts:
        if text.get_text() in ["Modelo", "Variante", "Categoria"]:
            text.set_weight("bold")
            if text.get_text() == "Variante":
                text.set_text("\nVariante")


# GENERACIÓN DE GRÁFICOS
def generar_graficas(df, col_tasa, col_confianza, carpeta_salida, es_juez=False):
    """
    Toma un conjunto de datos y genera una batería completa de visualizaciones.
    Es capaz de trabajar tanto con los datos brutos de evaluación de formato
    como con las métricas lógicas refinadas por el script del juez.
    """
    print(f"{Fore.CYAN}Generando gráficas en el directorio: {carpeta_salida}{Style.RESET_ALL}")
    os.makedirs(carpeta_salida, exist_ok=True)
    configurar_estilo()

    # Análisis de rendimiento dividiendo los problemas por su naturaleza intrínseca
    plt.figure()
    ax = sns.barplot(data=df, x="Modelo", y=col_tasa, hue="Categoria", palette=PALETA_CATEGORIAS, errorbar=None)
    for container in ax.containers: ax.bar_label(container, fmt='%.1f%%', padding=6, size=11)
    plt.title("Precisión por Categoría")
    plt.ylim(0, 105)
    plt.ylabel("Tasa de Acierto (%)")
    plt.xticks(rotation=15)
    estilizar_leyenda()
    plt.savefig(os.path.join(carpeta_salida, "Precision_Categoria.png"), bbox_inches='tight')
    plt.close()

    # Comparativa de impacto de las distintas estrategias de ingeniería de prompts
    plt.figure()
    ax = sns.barplot(data=df, x="Modelo", y=col_tasa, hue="Variante", hue_order=ORDEN_VARIANTES,
                     palette=PALETA_VARIANTES, errorbar=None)
    for container in ax.containers: ax.bar_label(container, fmt='%.1f%%', padding=6, size=11)
    plt.title("Efectividad de las Técnicas de Prompt")
    plt.ylim(0, 105)
    plt.ylabel("Tasa de Acierto (%)")
    plt.xticks(rotation=15)
    estilizar_leyenda()
    plt.savefig(os.path.join(carpeta_salida, "Precision_Variantes.png"), bbox_inches='tight')
    plt.close()

    # Evaluación de la calibración de la certeza declarada por el modelo
    plt.figure()
    ax = sns.barplot(data=df, x="Modelo", y=col_confianza, hue="Variante", hue_order=ORDEN_VARIANTES,
                     palette=PALETA_VARIANTES, errorbar=None)
    for container in ax.containers: ax.bar_label(container, fmt='%.1f%%', padding=6, size=11)
    plt.title("Confianza Media por Variante de Prompt")
    plt.ylim(0, 105)
    plt.ylabel("Confianza Media (%)")
    plt.xticks(rotation=15)
    estilizar_leyenda()
    plt.savefig(os.path.join(carpeta_salida, "Confianza_Variantes.png"), bbox_inches='tight')
    plt.close()

    # Cruce de datos para identificar los modelos más eficientes según su coste computacional
    df_agg_coste = df.groupby(["Modelo", "Variante"]).agg({"Tokens_Totales": "mean", col_tasa: "mean"}).reset_index()
    plt.figure()
    sns.scatterplot(data=df_agg_coste, x="Tokens_Totales", y=col_tasa, hue="Modelo", style="Variante",
                    style_order=ORDEN_VARIANTES, s=300, alpha=0.9, palette=PALETA_MODELOS)
    plt.title("Relación Coste vs Precisión")
    plt.xlabel("Tokens Promedio Consumidos por Prompt")
    plt.ylabel("Tasa de Acierto Promedio (%)")
    plt.ylim(0, 105)
    estilizar_leyenda()
    plt.savefig(os.path.join(carpeta_salida, "Coste_vs_Precision.png"), bbox_inches='tight')
    plt.close()

    # Detección de posibles sesgos cognitivos artificiales (Efecto Dunning-Kruger)
    df_agg_conf = df.groupby(["Modelo", "Variante"]).agg({col_confianza: "mean", col_tasa: "mean"}).reset_index()
    plt.figure()
    sns.scatterplot(data=df_agg_conf, x=col_confianza, y=col_tasa, hue="Modelo", style="Variante",
                    style_order=ORDEN_VARIANTES, s=300, alpha=0.9, palette=PALETA_MODELOS)
    plt.title("Relación Confianza vs Precisión")
    plt.xlabel("Confianza Media Reportada (%)")
    plt.ylabel("Tasa de Acierto Real (%)")
    plt.ylim(0, 105)
    estilizar_leyenda()
    plt.savefig(os.path.join(carpeta_salida, "Confianza_vs_Precision.png"), bbox_inches='tight')
    plt.close()

    # Visualización directa del gasto en tokens asociado a cada técnica de prompt
    plt.figure()
    ax = sns.barplot(data=df, x="Modelo", y="Tokens_Totales", hue="Variante", hue_order=ORDEN_VARIANTES,
                     palette=PALETA_VARIANTES, errorbar=None)
    for container in ax.containers: ax.bar_label(container, fmt='%.0f', padding=6, size=11)
    plt.title("Coste Computacional por Variante")
    plt.xlabel("Modelo")
    plt.ylabel("Tokens Promedio")
    plt.xticks(rotation=15)
    plt.ylim(0, df["Tokens_Totales"].max() * 1.15)
    estilizar_leyenda()
    plt.savefig(os.path.join(carpeta_salida, "Coste_Variantes.png"), bbox_inches='tight')
    plt.close()

    # Medición de la capacidad de procesamiento del hardware por cada modelo
    plt.figure()
    df_speed = df.groupby("Modelo")["Tokens_por_Segundo"].mean().reset_index()
    ax = sns.barplot(data=df_speed, y="Modelo", x="Tokens_por_Segundo", palette=PALETA_MODELOS, hue="Modelo",
                     dodge=False, errorbar=None)
    for container in ax.containers: ax.bar_label(container, fmt='%.1f', padding=6, size=11)
    plt.title("Velocidad Media de Generación")
    plt.xlabel("Tokens / Segundo")
    plt.ylabel("")
    plt.xlim(0, df_speed["Tokens_por_Segundo"].max() * 1.15)
    plt.savefig(os.path.join(carpeta_salida, "Velocidad_Hardware.png"), bbox_inches='tight')
    plt.close()

    # Experiencia de usuario final evaluando el tiempo de espera frente a la verbosidad
    df_agg_tiempo = df.groupby(["Modelo", "Variante"]).agg(
        {"Tokens_Totales": "mean", "Tiempo_Medio_s": "mean"}).reset_index()
    plt.figure()
    sns.scatterplot(data=df_agg_tiempo, x="Tokens_Totales", y="Tiempo_Medio_s", hue="Modelo", style="Variante",
                    style_order=ORDEN_VARIANTES, s=300, alpha=0.9, palette=PALETA_MODELOS)
    plt.title("Relación Tiempo de Espera vs Coste en Tokens")
    plt.xlabel("Tokens Promedio Consumidos por Prompt")
    plt.ylabel("Tiempo de Respuesta (Segundos)")
    estilizar_leyenda()
    plt.savefig(os.path.join(carpeta_salida, "Tiempo_vs_Tokens.png"), bbox_inches='tight')
    plt.close()

    # Gráfico exclusivo generado únicamente tras el análisis semántico del juez
    # Permite identificar qué modelos aciertan la lógica pero fallan siguiendo directrices de formato
    if es_juez and 'Discrepancia_Mayoria' in df.columns:
        plt.figure()
        df_disc = df.groupby("Modelo")["Discrepancia_Mayoria"].mean() * 100
        df_disc = df_disc.reset_index()
        ax = sns.barplot(data=df_disc, y="Modelo", x="Discrepancia_Mayoria", palette=PALETA_MODELOS, hue="Modelo",
                         dodge=False, errorbar=None)
        for container in ax.containers: ax.bar_label(container, fmt='%.1f%%', padding=6, size=11)
        plt.title("Tasa de Desobediencia de Formato")
        plt.xlabel("% de casos lógicamente correctos pero con mal formato")
        plt.ylabel("")
        max_disc = max(df_disc["Discrepancia_Mayoria"].max() * 1.2, 10)
        plt.xlim(0, max_disc)
        plt.savefig(os.path.join(carpeta_salida, "Tasa_Desobediencia.png"), bbox_inches='tight')
        plt.close()

    print(f"{Fore.GREEN}Imágenes procesadas y guardadas correctamente.{Style.RESET_ALL}\n")


# --- FLUJO PRINCIPAL ---

if __name__ == "__main__":
    print(f"{Fore.MAGENTA}--- INICIANDO GENERADOR DE GRÁFICAS ---{Style.RESET_ALL}")
    archivo = "resultados_benchmark.csv"

    if not os.path.exists(archivo):
        print(f"{Fore.RED}No se ha encontrado el archivo {archivo}. Ejecuta el benchmark primero.{Style.RESET_ALL}")
        exit()

    df = pd.read_csv(archivo)
    if df.empty:
        print(f"{Fore.RED}El archivo {archivo} no contiene datos.{Style.RESET_ALL}")
        exit()

    os.makedirs("graficos", exist_ok=True)

    # El primer lote representa el rendimiento basado puramente en la extracción estricta de formato
    generar_graficas(df, 'Tasa_Acierto_%', 'Confianza_Media_%', 'graficos/brutas', es_juez=False)

    # Si se ha ejecutado la validación avanzada, se genera el segundo lote mostrando la precisión real
    if 'Tasa_Acierto_Juez_%' in df.columns:
        df_juez = df.dropna(subset=['Tasa_Acierto_Juez_%'])
        if not df_juez.empty:
            generar_graficas(df_juez, 'Tasa_Acierto_Juez_%', 'Confianza_Media_%', 'graficos/juez', es_juez=True)
    else:
        print(
            f"{Fore.YELLOW}No se encontraron columnas del juez. Ejecuta el script del juez para un análisis más profundo.{Style.RESET_ALL}")

    print(f"{Fore.MAGENTA}--- PROCESO COMPLETADO ---{Style.RESET_ALL}")