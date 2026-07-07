import streamlit as st
from src.database.db_manager import get_current_inventory, get_store_city, get_product_weight
from src.agents.crew_setup import ejecutar_analisis
from src.config import CENTRAL_WAREHOUSE_CITY

st.set_page_config(page_title="RetailNova - Supply Chain AI", layout="wide")
st.title("RetailNova Group - Cadena de Suministro Inteligente")

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
    origin = CENTRAL_WAREHOUSE_CITY
    destination = city if city else CENTRAL_WAREHOUSE_CITY

    with st.spinner("Los agentes estan analizando la cadena de suministro..."):
        resultado = ejecutar_analisis(store_id, product_id, weight, origin, destination)

    st.success("Analisis completado")
    st.subheader("Decision Final")
    st.markdown(resultado.raw)

    with st.expander("Ver detalle del trabajo de cada agente"):
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
