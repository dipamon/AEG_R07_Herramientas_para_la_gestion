import json
from colorama import Fore, Style, init

# Inicializar colorama para asegurar que los colores de consola se reseteen automáticamente
init(autoreset=True)

# DEFINICIÓN DEL CORPUS DE PROBLEMAS
# Se define un dataset equilibrado de 16 problemas (8 matemáticos y 8 lógicos).
# Cada problema incluye una respuesta canónica ("esp") y tres niveles de dificultad semántica:
#   "c" (Control): Lenguaje natural, directo y sencillo.
#   "r" (Reimaginado): Mismo problema subyacente pero contextualizado en escenarios ficticios o técnicos.
#   "h" (Hardcore): Mismo problema ofuscado con jerga académica, técnica o científica compleja.

problemas_base = [
    # --- MATEMÁTICOS ---
    {"id": "M01", "cat": "matematico", "esp": "0",
     "c": "Si tienes 12 manzanas y repartes 3 a 4 amigos, ¿cuántas te quedan?",
     "r": "Eres gestor de satélites. Tienes 12 unidades de ancho de banda. Asignas 3 a cada una de las 4 estaciones. ¿Cuál es tu reserva final?",
     "h": "En un clúster cuántico con 12 PB de datos, el sistema distribuye bloques de 3 PB a 4 nodos secundarios. Ignorando la latencia, ¿cuántos PB útiles conserva el nodo principal?"},

    {"id": "M02", "cat": "matematico", "esp": "10",
     "c": "Un coche viaja a 60 km/h. ¿Cuántos kilómetros recorre en 10 minutos?",
     "r": "Un rover marciano avanza a 60 unidades por ciclo horario. ¿Qué distancia cubre en un sexto de ciclo?",
     "h": "El vector de velocidad escalar de una sonda es constante a 60 km/h en el vacío. Considerando una ventana de telemetría de 600 segundos, calcula el desplazamiento lineal total."},

    {"id": "M03", "cat": "matematico", "esp": "5",
     "c": "En una caja hay 3 bolas rojas y 2 azules. ¿Cuántas bolas hay en total?",
     "r": "En tu inventario mágico tienes 3 pociones de salud y 2 de maná. ¿Cuántos objetos posees?",
     "h": "Un contenedor de nivel 4 aloja 3 isótopos inestables alfa y 2 beta. Descartando la radiación de fondo, ¿cuál es el conteo neto de entidades radioactivas?"},

    {"id": "M04", "cat": "matematico", "esp": "24",
     "c": "Si un día tiene 24 horas, ¿cuántas horas hay en un día?",
     "r": "El ciclo de rotación de la Tierra dura 24 horas estándar. ¿Cuál es la duración de una rotación?",
     "h": "Teniendo en cuenta que el periodo sinódico planetario se divide en 24 segmentos cronológicos, ¿cuántos segmentos conforman un periodo ignorando bisiestos?"},

    {"id": "M05", "cat": "matematico", "esp": "50",
     "c": "Calcula la mitad de 100.",
     "r": "Un escudo de energía de 100 puntos se reduce a la mitad por un ataque. ¿Cuántos puntos quedan?",
     "h": "Un condensador de flujo de 100 MW sufre una atenuación de factor 0.5. Cuantifica la salida energética actual en MW."},

    {"id": "M06", "cat": "matematico", "esp": "4",
     "c": "¿Cuál es la raíz cuadrada de 16?",
     "r": "Tienes 16 drones y formas una cuadrícula perfecta. ¿Cuántos drones hay por lado?",
     "h": "Dado un espacio de dos dimensiones con un área superficial de 16 unidades cuadradas, determina la longitud exacta del vector ortogonal."},

    {"id": "M07", "cat": "matematico", "esp": "1",
     "c": "Si tienes 3 caramelos y te comes 2, ¿cuántos quedan?",
     "r": "La nave tiene 3 escudos. Tras recibir 2 impactos directos, ¿cuántos permanecen?",
     "h": "El sistema inmunológico despliega 3 fagocitos. Una incursión viral neutraliza a 2 mediante apoptosis. Especifica el saldo operativo."},

    {"id": "M08", "cat": "matematico", "esp": "15",
     "c": "Suma 10 y 5.",
     "r": "Ganas 10 puntos por explorar y 5 por luchar. ¿Cuánta experiencia tienes?",
     "h": "Un algoritmo incrementa su peso sináptico basal de 10 incorporando un delta de 5 unidades. Calcula el escalar del nodo."},

    # --- LÓGICOS ---
    {"id": "L01", "cat": "logico", "esp": "c",
     "c": "En la secuencia de letras 'a, b, c, a, b, d', ¿qué letra está justo después de la primera 'b'?",
     "r": "En la cola de procesos del servidor entran las tareas A, B, C, A, B, D. ¿Qué tarea se ejecuta inmediatamente tras la primera B?",
     "h": "Dada la cadena de secuencias alfanuméricas indexadas [a, b, c, a, b, d], identifica el elemento posicionado en el índice n+1, asumiendo que el primer elemento 'b' se encuentra en el índice n."},

    {"id": "L02", "cat": "logico", "esp": "segundo",
     "c": "En una carrera, adelantas al que va en segundo lugar. ¿En qué lugar vas tú ahora?",
     "r": "En un torneo de hackers, logras superar la puntuación del equipo que estaba en la posición dos. ¿Cuál es tu posición actual en el ranking?",
     "h": "Durante una competición de optimización algorítmica, tu sistema logra sobrepasar las métricas de latencia del agente clasificado en el percentil rank #2. Determina tu clasificación jerárquica actualizada."},

    {"id": "L03", "cat": "logico", "esp": "verde",
     "c": "La caja roja está dentro de la azul, y la verde está dentro de la roja. ¿Qué caja es la más pequeña?",
     "r": "El archivo RED está en la carpeta BLUE. El archivo GREEN está dentro del RED. ¿Cuál es el archivo de menor jerarquía?",
     "h": "El contenedor A encapsula al B, mientras que la subrutina C se ejecuta exclusivamente dentro de la sandbox de B. Identifica el nodo hoja en este árbol de dependencias (usando los colores originales rojo=B, azul=A, verde=C)."},

    {"id": "L04", "cat": "logico", "esp": "norte",
     "c": "Miras al norte, giras 90 grados a la derecha, luego 90 grados a la izquierda. ¿A dónde miras?",
     "r": "La nave apunta al Norte. El piloto gira a estribor 90º y luego a babor 90º. ¿Cuál es su vector de orientación final?",
     "h": "El giroscopio inicializa su acimut a 0º (Norte). Se le aplica un delta yaw de +90º, seguido de un delta yaw de -90º. Especifica el punto cardinal correspondiente a su vector resultante."},

    {"id": "L05", "cat": "logico", "esp": "miercoles",
     "c": "Si ayer fue lunes, ¿qué día es mañana?",
     "r": "El ciclo de guardado automático fue el Lunes (ciclo -1). ¿En qué día caerá el ciclo +1?",
     "h": "Si T-24 horas corresponde a la denominación temporal Lunes en el calendario gregoriano estándar, interpola la denominación nominal para T+24 horas."},

    {"id": "L06", "cat": "logico", "esp": "tio",
     "c": "El hermano de mi madre es mi...",
     "r": "El nodo paralelo conectado a mi nodo padre materno es mi...",
     "h": "En un grafo genealógico bidireccional, partiendo del nodo Ego, trazamos un arco ascendente al nodo Madre, y un arco lateral a su nodo Hermano. Define la relación de parentesco resultante."},

    {"id": "L07", "cat": "logico", "esp": "ana",
     "c": "Ana es más alta que Beatriz. Beatriz es más alta que Carmen. ¿Quién es la más alta?",
     "r": "La antena A tiene más señal que la B. La B tiene más señal que la C. ¿Cuál tiene la señal máxima?",
     "h": "Dados tres escalares de magnitud A, B y C. Si A > B y B > C, determina mediante transitividad matemática qué variable posee el valor supremo (responde con el nombre original Ana/Beatriz/Carmen)."},

    {"id": "L08", "cat": "logico", "esp": "si",
     "c": "Si todos los gatos maúllan y Michi es un gato, ¿Michi maúlla? (Responde 'si' o 'no')",
     "r": "Si todos los droides requieren recarga, y R2 es un droide, ¿R2 requiere recarga? (Responde 'si' o 'no')",
     "h": "Premisa 1: Para todo X que pertenece al conjunto F (Felinos), se cumple la función M(X). Premisa 2: El elemento 'Michi' es subconjunto estricto de F. ¿Es la evaluación booleana de M(Michi) verdadera? (Responde 'si' o 'no')"}
]

# TÉCNICAS DE MODIFICACIÓN DE PROMPT
# Se aplican patrones de Prompt Engineering para evaluar cómo reacciona el modelo a la redundancia y estructura:
# - original: Prompt base sin modificaciones.
# - duplicado: Repite el prompt dos veces seguidas para evaluar si el modelo consolida la atención.
# - repito: Introduce un conector natural ("Repito,") antes de la duplicación para guiar el flujo.
# - frase: Utiliza lenguaje analítico ("Reevaluando la premisa:") para inducir al modelo a un estado de razonamiento.

variaciones = [
    {"nombre": "original", "formato": "{}"},
    {"nombre": "duplicado", "formato": "{}\n{}"},
    {"nombre": "repito", "formato": "{}\nRepito,\n{}"},
    {"nombre": "frase", "formato": "{}\nReevaluando la premisa:\n{}"}
]

# GENERADOR DEL DATASET FINAL
datos_finales = []

for prob in problemas_base:
    # Mapeo de las dificultades para facilitar la iteración
    dificultades = {
        "control": prob["c"],
        "reimaginado": prob["r"],
        "hardcore": prob["h"]
    }

    # Iteramos sobre cada nivel de dificultad y aplicamos las técnicas de variación
    for dif_nombre, texto_dif in dificultades.items():
        for var in variaciones:
            # Construye el prompt final inyectando el texto del problema según el formato de la variación
            texto_final = var["formato"].format(texto_dif, texto_dif) if "{}\n" in var["formato"] else texto_dif

            # Se empaqueta cada prompt con su metainformación lista para la ejecución del benchmark
            datos_finales.append({
                "id_original": prob["id"],
                "categoria": prob["cat"],
                "dificultad": dif_nombre,
                "variante": var["nombre"],
                "problema_texto": texto_final,
                "solucion_esperada": prob["esp"]
            })

# Guardado seguro en disco manteniendo la codificación UTF-8 para caracteres especiales
with open("dataset_pruebas.json", "w", encoding="utf-8") as f:
    json.dump(datos_finales, f, indent=2, ensure_ascii=False)

print(
    f"{Fore.GREEN}¡'dataset_pruebas.json' generado con {len(datos_finales)} prompts listos para evaluar!{Style.RESET_ALL}")