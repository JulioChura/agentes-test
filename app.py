import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

# ------------------- RAG CON LANGCHAIN Y OLLAMA (LOCAL) -------------------
# Importaciones correctas para LangChain >= 0.3
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configurar embeddings locales
embedding_model = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Cargar y dividir el documento de políticas (con manejo de errores)
try:
    loader = TextLoader("politicas_empresa.txt", encoding="utf-8")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    # Crear la base de datos vectorial en memoria
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embedding_model,
        persist_directory="./chroma_db"  # guarda en disco para no repetir la creación
    )
    # Crear un retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    RAG_AVAILABLE = True
except Exception as e:
    st.error(f"Error al cargar la base de datos RAG: {e}")
    RAG_AVAILABLE = False
    retriever = None

# Herramienta RAG personalizada
@tool("Consultar politicas de la empresa (RAG)")
def consultar_politicas_rag(pregunta: str) -> str:
    """
    Busca en el documento de políticas de la empresa usando búsqueda semántica.
    Úsala cuando necesites saber las reglas de aprobación, categorías de productos,
    stock mínimo, tiempos de entrega, etc.
    """
    if not RAG_AVAILABLE or retriever is None:
        return "El sistema de políticas no está disponible. Verifica que el archivo politicas_empresa.txt exista y que Ollama esté corriendo."
    docs = retriever.invoke(pregunta)
    if not docs:
        return "No se encontró información relevante en las políticas."
    contexto = "\n".join([doc.page_content for doc in docs])
    return f"Información recuperada de las políticas:\n{contexto}"

# ---------------- CONFIGURACION DEL LLM LOCAL ----------------
llm = LLM(
    model="ollama/qwen3:4b",
    base_url="http://localhost:11434"
)

# ---------------- BASE DE DATOS ----------------
DB_PATH = "retailnova.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_current_inventory():
    conn = get_connection()
    query = """
        SELECT i.store_id, s.name as store_name, s.city,
               i.product_id, p.name as product_name, p.category, p.weight_kg,
               i.quantity, i.last_updated
        FROM inventory i
        JOIN stores s ON i.store_id = s.store_id
        JOIN products p ON i.product_id = p.product_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_sales_history(store_id, product_id, days=30):
    conn = get_connection()
    query = """
        SELECT quantity, sale_date
        FROM sales_history
        WHERE store_id = ? AND product_id = ?
        ORDER BY sale_date DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(store_id, product_id, days))
    conn.close()
    return df

def get_shipping_costs(origin, destination):
    conn = get_connection()
    query = """
        SELECT * FROM shipping_costs
        WHERE origin_city = ? AND destination_city = ?
    """
    df = pd.read_sql_query(query, conn, params=(origin, destination))
    conn.close()
    return df

def get_store_city(store_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT city FROM stores WHERE store_id = ?", (store_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_product_weight(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT weight_kg FROM products WHERE product_id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 1.0

# ---------------- HERRAMIENTAS DE CALCULO ----------------
@tool("Calcular pronostico de demanda")
def calcular_pronostico(store_id: int, product_id: int) -> str:
    """Calcula la demanda esperada para una tienda y producto basado en los ultimos 30 dias."""
    df = get_sales_history(store_id, product_id, 30)
    if df.empty:
        return f"No hay datos suficientes para tienda {store_id}, producto {product_id}."
    promedio = int(df['quantity'].mean())
    return f"Pronostico para tienda {store_id}, producto {product_id}: {promedio} unidades (ultimos 30 dias)."

@tool("Verificar stock actual")
def verificar_stock(store_id: int, product_id: int) -> str:
    """Consulta el stock actual de una tienda y producto."""
    df = get_current_inventory()
    mask = (df['store_id'] == store_id) & (df['product_id'] == product_id)
    row = df[mask]
    if row.empty:
        return f"No se encontro stock para tienda {store_id}, producto {product_id}."
    qty = row.iloc[0]['quantity']
    product = row.iloc[0]['product_name']
    return f"Stock actual de '{product}' en tienda {store_id}: {qty} unidades."

@tool("Calcular costo de envio")
def calcular_costo_envio(origin: str, destination: str, weight_kg: float) -> str:
    """Calcula el costo y tiempo de envio entre dos ciudades segun el peso."""
    df = get_shipping_costs(origin, destination)
    if df.empty:
        return f"No hay ruta disponible entre {origin} y {destination}."
    row = df.iloc[0]
    if weight_kg > 500:
        return f"Envio por CAMION: ${row['cost_large']}, {row['transit_days_large']} dias."
    else:
        return f"Envio por FURGONETA: ${row['cost_small']}, {row['transit_days_small']} dias."

# ---------------- AGENTES ----------------
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

# ---------------- TAREAS ----------------
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
        description=f"Para el faltante identificado, calcula el costo y tiempo de envio desde {origin_city} hasta {dest_city}. El peso del producto es {weight_kg} kg.",
        expected_output="Una opcion de envio con costo y tiempo de transito.",
        agent=agente_logistica
    )
    tarea_ejecutiva = Task(
        description="Revisa el costo del envio. Busca en el archivo de politicas de la empresa (usando la herramienta de consulta RAG) para saber si el envio se aprueba automaticamente o requiere autorizacion. Genera un resumen ejecutivo con la decision.",
        expected_output="Un resumen ejecutivo con la decision aprobada o rechazada, justificada con las politicas de la empresa.",
        agent=agente_ejecutivo
    )
    return [tarea_pronostico, tarea_inventario, tarea_logistica, tarea_ejecutiva]

# ---------------- STREAMLIT DASHBOARD ----------------
st.set_page_config(page_title="RetailNova - Supply Chain AI", layout="wide")
st.title("RetailNova Group - Cadena de Suministro Inteligente")

# Sidebar
st.sidebar.header("Seleccionar Analisis")
inventory_df = get_current_inventory()
stores = inventory_df[['store_id', 'store_name', 'city']].drop_duplicates()
products = inventory_df[['product_id', 'product_name', 'category', 'weight_kg']].drop_duplicates()

store_id = st.sidebar.selectbox(
    "Tienda",
    options=stores['store_id'].tolist(),
    format_func=lambda x: f"{stores[stores['store_id']==x]['store_name'].iloc[0]} ({stores[stores['store_id']==x]['city'].iloc[0]})"
)

product_id = st.sidebar.selectbox(
    "Producto",
    options=products['product_id'].tolist(),
    format_func=lambda x: f"{products[products['product_id']==x]['product_name'].iloc[0]} (Cat. {products[products['product_id']==x]['category'].iloc[0]})"
)
if st.sidebar.button("Ejecutar Analisis Completo"):
    city = get_store_city(store_id)
    weight = get_product_weight(product_id)
    origin = "Lima"
    destination = city if city else "Lima"

    with st.spinner("Los agentes están analizando la cadena de suministro..."):
        tasks = crear_tareas(store_id, product_id, weight, origin, destination)
        crew = Crew(
            agents=[agente_pronosticos, agente_inventarios, agente_logistica, agente_ejecutivo],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        resultado = crew.kickoff()

    st.success("✅ Análisis completado")

    # --- Mostrar solo la decisión final (raw) ---
    st.subheader("📋 Decisión Final")
    st.markdown(resultado.raw)  # <--- Esto muestra el texto bonito

    # --- Opcional: Ver detalles de cada agente en un expander ---
    with st.expander("🔍 Ver detalle del trabajo de cada agente"):
        for i, task_output in enumerate(resultado.tasks_output):
            st.write(f"**Agente {i+1}:** {task_output.agent}")
            st.write(task_output.raw)
            st.divider()

# Dashboard de KPIs
st.header("Dashboard de KPIs")
col1, col2, col3, col4 = st.columns(4)
total_stock = inventory_df['quantity'].sum()
stores_low = len(inventory_df[inventory_df['quantity'] < 50])
total_products = len(products)
col1.metric("Tiendas", len(stores))
col2.metric("Stock Total", f"{total_stock:,} unidades")
col3.metric("Tiendas con bajo stock", stores_low)
col4.metric("Productos", total_products)

st.subheader("Stock por Tienda (Top 10)")
stock_by_store = inventory_df.groupby('store_name')['quantity'].sum().sort_values(ascending=False).head(10)
st.bar_chart(stock_by_store)

st.subheader("Inventario Detallado")
search = st.text_input("Buscar por tienda o producto")
if search:
    filtered = inventory_df[
        inventory_df['store_name'].str.contains(search, case=False) |
        inventory_df['product_name'].str.contains(search, case=False)
    ]
    st.dataframe(filtered)
else:
    st.dataframe(inventory_df.head(100))