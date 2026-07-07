from crewai.tools import tool
from src.database.db_manager import get_sales_history, get_current_inventory, get_shipping_costs

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
    category = row.iloc[0]['category']  # <--- Obtener la categoría
    return f"Stock actual de '{product}' (Cat. {category}) en tienda {store_id}: {qty} unidades."

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