from crewai import Agent, Task, Crew, Process, LLM
from src.config import OLLAMA_BASE_URL, LLM_MODEL
from src.agents.tools import calcular_pronostico, verificar_stock, calcular_costo_envio
from src.rag.vector_store import consultar_politicas_rag, RAG_AVAILABLE
from src.config import GEMINI_KEY_1, GEMINI_KEY_2  


llm = LLM(
    model=f"ollama/{LLM_MODEL}",
    base_url=OLLAMA_BASE_URL
)

llm_agente1 = LLM(
    model="gemini/gemini-2.5-flash",  
    api_key=GEMINI_KEY_1
)

llm_agente2 = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=GEMINI_KEY_2
)

llm_agente3 = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=GEMINI_KEY_1 
)

llm_agente4 = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=GEMINI_KEY_2  
)

agente_pronosticos = Agent(
    role="Analista de Pronosticos",
    goal="Predecir la demanda de productos por tienda usando datos historicos.",
    backstory="Eres un experto en series temporales y analisis de datos.",
    tools=[calcular_pronostico],
    llm=llm,
    verbose=True
)

agente_inventarios = Agent(
    role="Especialista en Inventarios",
    goal="Comparar el stock actual con la demanda pronosticada y detectar faltantes.",
    backstory="Eres un experto en gestion de inventarios.",
    tools=[verificar_stock],
    llm=llm,
    verbose=True
)

agente_logistica = Agent(
    role="Optimizador de Logistica",
    goal="Calcular la ruta y costo de envio mas eficiente para cada pedido.",
    backstory="Eres un experto en cadena de suministro.",
    tools=[calcular_costo_envio],
    llm=llm,
    verbose=True
)

agente_ejecutivo = Agent(
    role="Gerente de Operaciones",
    goal="Tomar la decision final sobre los envios basado en politicas y presupuesto. Usa la herramienta de busqueda de politicas para consultar las reglas de la empresa.",
    backstory="Eres el responsable de aprobar o rechazar los envios. Debes basar tus decisiones en las politicas de la empresa.",
    tools=[consultar_politicas_rag] if RAG_AVAILABLE else [],
    llm=llm,
    verbose=True
)

def crear_tareas(store_id, product_id, weight_kg, origin_city, dest_city):
    tarea_pronostico = Task(
        description=f"Analiza las ventas historicas de los ultimos 30 dias para la tienda {store_id} y el producto {product_id}. Calcula la demanda esperada.",
        expected_output="Un numero entero con la cantidad de unidades pronosticadas.",
        agent=agente_pronosticos
    )
    tarea_inventario = Task(
        description=f"Verifica el stock actual de la tienda {store_id} para el producto {product_id}. Compara con el pronostico y determina si hay faltante.",
        expected_output="Un mensaje indicando el stock actual y si hay faltante.",
        agent=agente_inventarios
    )
    tarea_logistica = Task(
        description=f"""Revisa si hay faltante de stock. 
        - Si NO hay faltante (stock suficiente), responde EXACTAMENTE: "No se requiere envio, stock suficiente."
        - Si HAY faltante, calcula el costo y tiempo de envio desde {origin_city} hasta {dest_city}. El peso del producto es {weight_kg} kg.
        """,
        expected_output="'No se requiere envio' O una opcion de envio con costo y tiempo.",
        agent=agente_logistica
    )
    tarea_ejecutiva = Task(
        description="""Revisa el contexto completo. 
        - Si el Agente de Logistica dijo 'No se requiere envio', entonces genera un resumen ejecutivo indicando que el stock es suficiente y no se requiere ninguna accion.
        - Si el Agente de Logistica dio una opcion de envio (costo y tiempo), entonces busca en el archivo de politicas de la empresa (usando la herramienta de consulta RAG) para saber si el envio se aprueba automaticamente o requiere autorizacion.
        **IMPORTANTE**: Usa la categoría del producto del contexto para aplicar la politica de prioridad.
        """,
        expected_output="Un resumen ejecutivo indicando 'No se requiere envio' O la decision aprobada/rechazada con justificacion.",
        agent=agente_ejecutivo
    )
    return [tarea_pronostico, tarea_inventario, tarea_logistica, tarea_ejecutiva]

def ejecutar_analisis(store_id, product_id, weight_kg, origin_city, dest_city):
    tasks = crear_tareas(store_id, product_id, weight_kg, origin_city, dest_city)
    crew = Crew(
        agents=[agente_pronosticos, agente_inventarios, agente_logistica, agente_ejecutivo],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    return crew.kickoff()
