import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "retailnova.db"

def create_tables(conn):
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS stores;
        CREATE TABLE stores (
            store_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            region TEXT NOT NULL
        );

        DROP TABLE IF EXISTS products;
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            price REAL NOT NULL
        );

        DROP TABLE IF EXISTS inventory;
        CREATE TABLE inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            last_updated DATE NOT NULL,
            FOREIGN KEY (store_id) REFERENCES stores(store_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        DROP TABLE IF EXISTS sales_history;
        CREATE TABLE sales_history (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            sale_date DATE NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (store_id) REFERENCES stores(store_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        DROP TABLE IF EXISTS shipping_costs;
        CREATE TABLE shipping_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_city TEXT NOT NULL,
            destination_city TEXT NOT NULL,
            cost_small REAL NOT NULL,
            cost_large REAL NOT NULL,
            transit_days_small INTEGER NOT NULL,
            transit_days_large INTEGER NOT NULL
        );
    """)
    conn.commit()

def populate_stores(conn):
    cursor = conn.cursor()
    cities = [
        ("Lima", "Peru", "Centro"),
        ("Arequipa", "Peru", "Sur"),
        ("Trujillo", "Peru", "Norte"),
        ("Cusco", "Peru", "Sur"),
        ("Bogota", "Colombia", "Centro"),
        ("Medellin", "Colombia", "Norte"),
        ("Cali", "Colombia", "Sur"),
        ("Santiago", "Chile", "Sur"),
        ("Buenos Aires", "Argentina", "Sur"),
        ("Montevideo", "Uruguay", "Sur")
    ]
    for i in range(1, 301):
        city = random.choice(cities)
        cursor.execute(
            "INSERT INTO stores (store_id, name, city, country, region) VALUES (?, ?, ?, ?, ?)",
            (i, f"Tienda {i}", city[0], city[1], city[2])
        )
    conn.commit()

def populate_products(conn):
    cursor = conn.cursor()
    products = [
        ("Leche Entera 1L", "A", 1.0, 3.50),
        ("Pan Molde 500g", "A", 0.5, 2.80),
        ("Huevos (docena)", "A", 0.6, 4.20),
        ("Arroz 1kg", "B", 1.0, 2.30),
        ("Aceite 1L", "B", 0.9, 5.10),
        ("Azucar 1kg", "B", 1.0, 1.80),
        ("Cafe 500g", "C", 0.5, 8.90),
        ("Cereal 400g", "C", 0.4, 6.50),
        ("Fideos 500g", "B", 0.5, 2.10),
        ("Jabon Liquido", "C", 1.2, 4.50),
        ("Detergente", "C", 1.0, 3.20),
        ("Papel Higienico 4un", "B", 0.8, 5.00),
        ("Galletas 200g", "C", 0.2, 2.50),
        ("Atun 170g", "B", 0.17, 4.80),
        ("Mayonesa 500g", "C", 0.5, 3.60),
        ("Salsa de Tomate 500g", "C", 0.5, 2.90),
        ("Harina 1kg", "B", 1.0, 1.50),
        ("Leche Condensada", "C", 0.4, 3.20),
        ("Cocoa 250g", "C", 0.25, 6.00),
        ("Mermelada 500g", "C", 0.5, 4.10),
        ("Queso 250g", "A", 0.25, 5.50),
        ("Yogur 1L", "A", 1.0, 4.00),
        ("Jugo 1L", "C", 1.0, 3.30),
        ("Agua 2L", "B", 2.0, 1.80),
        ("Gaseosa 2L", "B", 2.0, 2.50),
        ("Cerveza 6un", "C", 2.5, 12.00),
        ("Vino Tinto 750ml", "C", 1.2, 15.00),
        ("Aceitunas 200g", "C", 0.2, 4.00),
        ("Alcaparras 100g", "C", 0.1, 5.00),
        ("Vinagre 500ml", "C", 0.5, 2.00),
        ("Aceite de Oliva 500ml", "C", 0.5, 10.00),
        ("Miel 500g", "C", 0.5, 8.00),
        ("Dulce de Leche 400g", "C", 0.4, 4.50),
        ("Crema de Leche 200ml", "C", 0.2, 3.00),
        ("Leche de Coco 400ml", "C", 0.4, 3.50),
        ("Conserva de Pescado", "C", 0.3, 5.00),
        ("Sopa Instantanea", "C", 0.1, 1.20),
        ("Pure de Papa", "C", 0.5, 2.80),
        ("Galletas de Sal", "C", 0.3, 2.00),
        ("Chocolate 100g", "C", 0.1, 3.00),
        ("Caramelo 200g", "C", 0.2, 2.50),
        ("Chicles", "C", 0.1, 1.50),
        ("Agua Mineral 500ml", "C", 0.5, 1.00),
        ("Refresco en Polvo", "C", 0.2, 1.80),
        ("Cafe Instantaneo", "C", 0.1, 6.00),
        ("Te 25un", "C", 0.1, 4.50),
        ("Leche sin Lactosa 1L", "B", 1.0, 5.00),
        ("Queso Crema 200g", "B", 0.2, 4.50),
        ("Yogur Griego 400g", "B", 0.4, 5.50),
        ("Jamon 200g", "A", 0.2, 6.00)
    ]
    for idx, (name, cat, weight, price) in enumerate(products, 1):
        cursor.execute(
            "INSERT INTO products (product_id, name, category, weight_kg, price) VALUES (?, ?, ?, ?, ?)",
            (idx, name, cat, weight, price)
        )
    conn.commit()

def populate_inventory(conn):
    cursor = conn.cursor()
    # Para cada tienda y cada producto, stock aleatorio entre 20 y 500
    for store_id in range(1, 301):
        for product_id in range(1, 51):
            qty = random.randint(20, 500)
            cursor.execute(
                "INSERT INTO inventory (store_id, product_id, quantity, last_updated) VALUES (?, ?, ?, ?)",
                (store_id, product_id, qty, datetime.now().date())
            )
    conn.commit()

def populate_sales_history(conn):
    cursor = conn.cursor()
    start_date = datetime.now() - timedelta(days=1095)  # 3 anos
    for day in range(1095):
        current_date = start_date + timedelta(days=day)
        # Cada dia, para cada tienda y producto, genera una venta aleatoria
        for store_id in range(1, 301):
            for product_id in range(1, 51):
                # Demanda base
                base = random.randint(0, 20)
                # Promociones (10% de los dias)
                if random.random() < 0.1:
                    base = int(base * 2)
                # Fines de semana aumentan 30%
                if current_date.weekday() in [5, 6]:
                    base = int(base * 1.3)
                # Variacion estacional (simplificada)
                if current_date.month in [12, 1, 7]:  # meses de alta venta
                    base = int(base * 1.2)
                if base > 0:
                    cursor.execute(
                        "INSERT INTO sales_history (store_id, product_id, sale_date, quantity) VALUES (?, ?, ?, ?)",
                        (store_id, product_id, current_date, base)
                    )
    conn.commit()

def populate_shipping_costs(conn):
    cursor = conn.cursor()
    cities = ["Lima", "Arequipa", "Trujillo", "Cusco", "Bogota", "Medellin", "Cali", "Santiago", "Buenos Aires", "Montevideo"]
    for origin in cities:
        for dest in cities:
            if origin == dest:
                continue
            cost_small = round(random.uniform(50, 200), 2)
            cost_large = round(random.uniform(100, 400), 2)
            days_small = random.randint(1, 3)
            days_large = random.randint(2, 5)
            cursor.execute(
                "INSERT INTO shipping_costs (origin_city, destination_city, cost_small, cost_large, transit_days_small, transit_days_large) VALUES (?, ?, ?, ?, ?, ?)",
                (origin, dest, cost_small, cost_large, days_small, days_large)
            )
    conn.commit()

def create_policies_file():
    content = """=== POLITICAS DE CADENA DE SUMINISTRO - RETAILNOVA GROUP ===

1. POLITICA DE APROBACION DE ENVIOS
   - Si el costo total del envio es MENOR a $1,000: APROBACION AUTOMATICA.
   - Si el costo total es MAYOR o IGUAL a $1,000: REQUIERE AUTORIZACION DEL GERENTE.
   - Si el costo supera los $5,000: REQUIERE APROBACION DEL DIRECTORIO.

2. POLITICA DE PRIORIDAD DE PRODUCTOS
   - Productos Categoria "A": Siempre usar envio RAPIDO (aunque cueste mas).
   - Productos Categoria "B": Usar envio estandar (balance costo/tiempo).
   - Productos Categoria "C": Usar envio mas BARATO disponible.

3. POLITICA DE STOCK MINIMO
   - Cada tienda debe mantener stock minimo para 7 dias de venta promedio.
   - Si el stock baja a menos de 3 dias, se activa ALERTA ROJA.

4. POLITICA DE PROVEEDORES
   - El tiempo maximo de entrega de un proveedor es 5 dias habiles.
   - Si un proveedor falla 3 entregas consecutivas, se busca alternativo.

5. POLITICA DE DEVOLUCIONES
   - Las devoluciones de productos danados deben procesarse en maximo 48 horas.
"""
    with open("politicas_empresa.txt", "w", encoding="utf-8") as f:
        f.write(content)

def main():
    print("Creando base de datos y archivo de politicas...")
    conn = sqlite3.connect(DB_NAME)
    create_tables(conn)
    populate_stores(conn)
    populate_products(conn)
    populate_inventory(conn)
    populate_sales_history(conn)
    populate_shipping_costs(conn)
    conn.close()
    create_policies_file()
    print("Base de datos 'retailnova.db' y 'politicas_empresa.txt' creados exitosamente.")

if __name__ == "__main__":
    main()