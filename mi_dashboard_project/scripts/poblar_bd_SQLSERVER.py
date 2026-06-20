# %%
import pandas as pd
# Librería para SQL Server
import pyodbc
# %%
# === 1) Cargar el CSV ===
df = pd.read_csv(r"C:\Proyectos Power BI 2025\mi_dashboard_project\data\consumer_data.csv")

# %%
# Normalizar strings (evita problemas de espacios)
for col in df.columns:
    if df[col].dtype == 'object':     # Verificar si la columna es de tipo texto (object).Esto es importante porque .str.strip() solo funciona con strings
        df[col] = df[col].str.strip()  # Eliminar espacios en blanco al inicio y al final de cada valor. Ayuda a evitar problemas al comparar o insertar datos en la base de datos

# %%
# === 2) Conexión a SQL Server ===
conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=FIORELLARO98;"   
    "DATABASE=consumer_behavior;"
    "Trusted_Connection=yes;"
)

print(conn)

cursor = conn.cursor() #cursor dentro de la base de datos. Ejecuta y apunta filas de resultados

# %%
# ===== helper: inserta único y devuelve ID =====

def get_dim_id(table, col, value):

    # La máquina necesita saber: 1) Dónde buscar (tabla), 2) Qué columna revisar (col), 3) Qué valor buscar (value).

    # Cambiamos el nombre de la columna ID a solo 'gender_id'
    # Usamos .replace('dim_', '') para quitar el prefijo 'dim_'
    id_col = table.replace('dim_', '') + '_id'

    # 1. BUSCAR: Pregunta a la base de datos si el valor ya existe.
    cursor.execute(
        f"SELECT {id_col} FROM {table} WHERE {col} = ?",
        (value,)
    )

    result = cursor.fetchone()        # 2. OBTENER: Trae la primera fila (el ID) si existe, o trae "Nada" (None) si no.

    if result:       # 3. VERIFICAR: Si el resultado NO fue "Nada" (o sea, si ya lo encontró)...
        return result[0]    # 4. DEVOLVER: Entrega el ID (el número) y se detiene aquí.

    # ✅ CAMBIO: Se reemplazó el INSERT separado + SCOPE_IDENTITY() por un INSERT con OUTPUT INSERTED.
    # El problema original era que SCOPE_IDENTITY() se ejecutaba en un scope distinto al INSERT,
    # devolviendo NULL. Con OUTPUT INSERTED.{id_col} el ID se obtiene dentro del mismo INSERT,
    # garantizando que siempre retorne el valor correcto.
    cursor.execute(
        f"INSERT INTO {table} ({col}) OUTPUT INSERTED.{id_col} VALUES (?)",
        (value,)
    )

    row_inserted = cursor.fetchone()  # OUTPUT devuelve directamente la fila con el ID insertado

    conn.commit()    # 6. GUARDAR: Le pide a la base de datos que guarde el cambio de forma permanente.

    # 7. NUEVO ID: Devuelve el ID que la base de datos le acaba de dar al valor recién insertado.
    return int(row_inserted[0])

# %%
# === 3) Recorrer registros ===
for _, row in df.iterrows(): # Empieza el ciclo: procesar cada fila de datos del CSV.

    # 1. OBTENCIÓN DE IDs SIMPLES (Usando la función "Buscar o Insertar")
    # Busca/Inserta el GÉNERO de la fila actual y guarda su ID.
    gender_id = get_dim_id("dim_gender", "gender_name", row["Gender"])
    loc_id = get_dim_id("dim_location", "location_name", row["Location"])
    item_id = get_dim_id("dim_item", "item_name", row["Item Purchased"])
    category_id = get_dim_id("dim_category", "category_name", row["Category"])
    size_id = get_dim_id("dim_size", "size_name", row["Size"])
    color_id = get_dim_id("dim_color", "color_name", row["Color"])
    season_id = get_dim_id("dim_season", "season_name", row["Season"])

    subs_id = get_dim_id(
        "dim_subscription_status",
        "subscription_status_name",
        row["Subscription Status"]
    )

    ship_id = get_dim_id(
        "dim_shipping_type",
        "shipping_type_name",
        row["Shipping Type"]
    )

    discount_id = get_dim_id(
        "dim_discount_status",
        "discount_status_name",
        row["Discount Applied"]
    )

    promo_id = get_dim_id(
        "dim_promo_status",
        "promo_status_name",
        row["Promo Code Used"]
    )

    paym_id = get_dim_id(
        "dim_payment_method",
        "payment_method_name",
        row["Payment Method"]
    )

    freq_id = get_dim_id(
        "dim_frequency",
        "frequency_name",
        row["Frequency of Purchases"]
    )

    # 2. DIMENSIÓN COMPUESTA: EL PRODUCTO
    # PRODUCT combina item + category + size + color

    # Intenta encontrar el ID de producto buscando la combinación de los 4 IDs que ya tenemos.
    cursor.execute(
        """
        SELECT product_id
        FROM dim_product
        WHERE item_id = ?
        AND category_id = ?
        AND size_id = ?
        AND color_id = ?
        """,
        (item_id, category_id, size_id, color_id)
    )

    prod = cursor.fetchone()

    if prod: # Si la variable 'prod' tiene algo (o sea, si el producto ya existe)...
        product_id = prod[0]  # ...toma el ID que encontró (el número dentro de la tupla).

    else:  # Si el producto (la combinación de 4 IDs) NO existe...

        # ✅ CAMBIO: Igual que en get_dim_id, se reemplazó INSERT + SCOPE_IDENTITY() separados
        # por INSERT con OUTPUT INSERTED.product_id para obtener el ID en el mismo batch
        # y evitar que fetchone()[0] devuelva None.
        cursor.execute(
            """
            INSERT INTO dim_product (item_id, category_id, size_id, color_id)
            OUTPUT INSERTED.product_id
            VALUES (?, ?, ?, ?)
            """,
            (item_id, category_id, size_id, color_id)
        )

        product_id = int(cursor.fetchone()[0])  # OUTPUT devuelve el ID directamente

        conn.commit() # Guardamos la nueva combinación en la base de datos.

    # CUSTOMER
    birth_year = 2025 - int(row["Age"])  # Calcula el año de nacimiento (resta la edad de 2025).

    # Busca en la tabla dim_customer si este cliente ya existe (usando su ID del CSV).
    cursor.execute(
        "SELECT customer_id FROM dim_customer WHERE customer_id = ?",
        (row["Customer ID"],)
    )

    c = cursor.fetchone() # Trae el resultado: el ID si existe, o 'Nada' (None) si es un cliente nuevo.

    if not c: # Si 'c' es 'Nada' (es decir, el cliente NO ha sido insertado antes)...

        # ...entonces, inserta al cliente con todos sus datos (ID, año, IDs de Género y Ubicación).
        cursor.execute(
            """
            INSERT INTO dim_customer
            (customer_id, birth_year, gender_id, location_id)
            VALUES (?, ?, ?, ?)
            """,
            (
                row["Customer ID"],
                birth_year,
                gender_id,
                loc_id
            )
        )

        conn.commit()  # Guarda este nuevo cliente de forma permanente en la base de datos.

    # FACT
    cursor.execute(  # Le decimos a la base de datos que guarde una nueva transacción.

        """
        INSERT INTO fact_transactions
        (
            customer_id,
            product_id,
            season_id,
            subscription_status_id,
            shipping_type_id,
            discount_status_id,
            promo_status_id,
            payment_method_id,
            frequency_id,
            purchase_amount_usd,
            previous_purchases,
            review_rating
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            # CLAVES FORÁNEAS (IDs de las Tablas de Dimensión)
            row["Customer ID"],
            product_id,
            season_id,
            subs_id,
            ship_id,
            discount_id,
            promo_id,
            paym_id,
            freq_id,

            # MÉTRICAS (Valores Numéricos directos del CSV)
            row["Purchase Amount (USD)"],
            row["Previous Purchases"],
            row["Review Rating"]
        )
    )

    conn.commit()

# %%
print("✅ PROCESO COMPLETO — datos cargados a SQL Server!")

cursor.close()  # Cierra el cursor
conn.close()  # Cierra la conexión a la base de datos para liberar recursos.

# %%