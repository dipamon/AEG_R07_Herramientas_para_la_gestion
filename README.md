# Optimización de Resultados en SLMs mediante la Duplicación de Prompts

Este proyecto es una suite semi-automatizada de investigación diseñada para comprobar empíricamente una técnica de *Prompt Engineering* conocida como **Redundancia Estratégica**. 

Inspirado en la publicación *"Prompt Repetition Improves Non-Reasoning LLMs"* de investigadores de Google, este repositorio evalúa si la repetición sistemática de instrucciones mitiga los problemas de ventana de contexto (*Lost in the Middle* y *Recency Bias*) en Modelos de Lenguaje Pequeños (Small Language Models o SLMs), ayudándoles a mejorar su precisión en problemas lógicos y matemáticos sin necesidad de capacidades nativas de *Chain-of-Thought*.

## Arquitectura de Evaluación

El proyecto no busca simplemente comparar qué modelo es "el mejor", sino analizar su comportamiento ante cuatro variaciones del mismo *prompt*:
* **Original**: Instrucción base.
* **Duplicado**: La instrucción se repite dos veces seguidas.
* **Repito**: Se duplica la instrucción introduciendo el conector "Repito,".
* **Frase**: Se duplica introduciendo "Reevaluando la premisa:".

Para garantizar que los modelos no sean penalizados por fallos de formato si su lógica interna es correcta, se ha implementado un sistema de validación híbrida:
* **Extracción Estricta (Regex)**: Un motor inicial comprueba si el modelo siguió la orden de formato a la perfección.
* **LLM-as-a-Judge (Juez Semántico)**: Un modelo supervisor lee las respuestas que fallaron la validación estricta y determina, mediante *Few-Shot Prompting*, si la matemática o lógica subyacente era correcta. La diferencia entre ambas validaciones genera la métrica de **Tasa de Desobediencia (Discrepancia)**.

## Modelos Evaluados

Se han seleccionado cinco modelos de menos de 4 billones de parámetros para su ejecución en hardware local. Esta diversidad arquitectónica permite comprobar si el efecto de la redundancia es universal.

* **Llama 3.2 3B** (Meta): Modelo instructivo estándar de la industria. Utilizado también como el "Juez Semántico" del proyecto por su alta capacidad de razonamiento lógico.
* **Qwen 2.5 3B** (Alibaba Cloud): Variante instructiva entrenada intensivamente en datos lógicos y matemáticos.
* **Ministral 3B** (Mistral AI): Modelo optimizado para dispositivos de bajo consumo y tareas de *edge computing*.
* **LFM 2.5 1.2B** (Liquid AI): Modelo fundamentado en arquitecturas no convencionales (Liquid Foundation Models / Sistemas dinámicos).
* **TinyLlama 1.1B** (TinyLlama): Modelo ultra-ligero que condensa la arquitectura Llama 2 en una escala mínima.

## Estructura del Repositorio

El flujo de trabajo se divide en cuatro scripts independientes y secuenciales ubicados en la carpeta `codigo/`:

* `00_generador_prompts.py`: Construye el corpus de pruebas de 45 iteraciones (combinando problemas lógicos/matemáticos, dificultades y variantes de repetición).
* `01_main.py`: Motor de inferencia local. Se conecta a la API, inyecta los prompts con ejemplos (*Few-Shot*) y realiza la recolección estricta.
* `02_juez.py`: Sistema de auditoría semántica. Aplica el filtro *Fast-Eval* y realiza consultas al Juez LLM para recalcular los aciertos y la discrepancia.
* `03_generador_graficos.py`: Módulo de visualización avanzada que procesa los CSV y genera los gráficos de alta resolución en la carpeta `graficos/`.

## Requisitos y Configuración del Entorno

Este proyecto utiliza **uv** como gestor de paquetes ultrarrápido para Python y **LM Studio** para servir los modelos localmente.

### 1. Clonar y configurar el entorno Python
Clona este repositorio en tu máquina local y utiliza `uv` para sincronizar las dependencias exactas desde el archivo `uv.lock`.

```bash
git clone <url-del-repositorio>
cd AEG_R07_Herramientas_para_la_gestion
uv sync
```

## 2. Configurar LM Studio
* Descarga e instala LM Studio.
* Descarga los modelos mencionados anteriormente en formato GGUF (cuantizados para tu hardware).
* Dirígete a la pestaña Local Server (Servidor Local).
* Asegúrate de que el servidor está corriendo en el puerto por defecto: http://localhost:1234/v1.

### **Pasos para replicar el experimento**
Para ejecutar la suite completa de forma correcta, sigue este orden:
1. Activa tu entorno virtual gestionado por uv (source .venv/bin/activate o equivalente en tu SO).
2. Navega a la carpeta de código: cd codigo
3. Genera el dataset: ejecuta python 00_generador_prompts.py. Se creará un archivo dataset_pruebas.json.
4. Carga el primer modelo a evaluar en LM Studio.
5. Ejecuta el benchmark: python 01_main.py. Selecciona el modelo correspondiente en el menú interactivo. Cuando termine, el script guardará los datos en resultados_benchmark.csv.
6. Repite los pasos 4 y 5 para cada uno de los modelos que desees testear. Pulsa 0 en el menú interactivo para salir cuando hayas terminado con todos.
7. Cambia el modelo en LM Studio y carga Llama 3.2 3B Instruct (o tu modelo más inteligente) para que actúe como Juez.
8. Ejecuta la validación semántica: python 02_juez.py. El script auditará el CSV y sobrescribirá los datos con la precisión lógica real.
9. Genera el análisis visual: python 03_generador_graficos.py.

En la carpeta graficos/ encontrarás dos subcarpetas: brutas (rendimiento basado únicamente en la obediencia al formato) y juez (rendimiento basado en el acierto lógico real, incluyendo el análisis de desobediencia y el cruce del coste de tokens frente al tiempo de respuesta).
