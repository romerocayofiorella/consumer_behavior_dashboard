# %%
import pandas as pd
import pyodbc

# %%
# 1. Cargar y normalizar el dataset
df = pd.read_csv(r"C:\Proyectos Power BI 2025\mi_dashboard_project\data\consumer_data.csv")

for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].str.strip()

# %%
# 2. Conexión a SQL Server
conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=FIORELLARO98;"
    "DATABASE=consumer_behavior;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

# %%
# 3. Función helper: busca un valor en una tabla de dimensión y retorna su ID.
#    Si no existe, lo inserta y retorna el ID generado.
def get_dim_id(table, col, value):
    id_col = table.replace('dim_', '') + '_id'

    cursor.execute(f"SELECT {id_col} FROM {table} WHERE {col} = ?", (value,))
    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute(
        f"INSERT INTO {table} ({col}) OUTPUT INSERTED.{id_col} VALUES (?)",
        (value,)
    )
    row_inserted = cursor.fetchone()
    conn.commit()

    return int(row_inserted[0])

# %%
# 4. Recorrer cada registro del CSV e insertar en las tablas de dimensión y hechos
for _, row in df.iterrows():

    # Dimensiones simples
    gender_id   = get_dim_id("dim_gender", "gender_name", row["Gender"])
    loc_id      = get_dim_id("dim_location","location_name", row["Location"])
    item_id     = get_dim_id("dim_item","item_name", row["Item Purchased"])
    category_id = get_dim_id("dim_category","category_name", row["Category"])
    size_id     = get_dim_id("dim_size","size_name", row["Size"])
    color_id    = get_dim_id("dim_color","color_name", row["Color"])
    season_id   = get_dim_id("dim_season", "season_name", row["Season"])
    subs_id     = get_dim_id("dim_subscription_status","subscription_status_name", row["Subscription Status"])
    ship_id     = get_dim_id("dim_shipping_type","shipping_type_name", row["Shipping Type"])
    discount_id = get_dim_id("dim_discount_status","discount_status_name", row["Discount Applied"])
    promo_id    = get_dim_id("dim_promo_status","promo_status_name", row["Promo Code Used"])
    paym_id     = get_dim_id("dim_payment_method","payment_method_name", row["Payment Method"])
    freq_id     = get_dim_id("dim_frequency","frequency_name", row["Frequency of Purchases"])

    # Dimensión compuesta: producto (combinación única de item + categoría + talla + color)
    cursor.execute(
        """
        SELECT product_id FROM dim_product
        WHERE item_id = ? AND category_id = ? AND size_id = ? AND color_id = ?
        """,
        (item_id, category_id, size_id, color_id)
    )
    prod = cursor.fetchone()

    if prod:
        product_id = prod[0]
    else:
        cursor.execute(
            """
            INSERT INTO dim_product (item_id, category_id, size_id, color_id)
            OUTPUT INSERTED.product_id
            VALUES (?, ?, ?, ?)
            """,
            (item_id, category_id, size_id, color_id)
        )
        product_id = int(cursor.fetchone()[0])
        conn.commit()

    # Cliente: se inserta solo si no existe previamente
    birth_year = 2025 - int(row["Age"])
    cursor.execute("SELECT customer_id FROM dim_customer WHERE customer_id = ?", (row["Customer ID"],))

    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO dim_customer (customer_id, birth_year, gender_id, location_id)
            VALUES (?, ?, ?, ?)
            """,
            (row["Customer ID"], birth_year, gender_id, loc_id)
        )
        conn.commit()

    # Tabla de hechos: una fila por transacción
    cursor.execute(
        """
        INSERT INTO fact_transactions (
            customer_id, product_id, season_id,
            subscription_status_id, shipping_type_id, discount_status_id,
            promo_status_id, payment_method_id, frequency_id,
            purchase_amount_usd, previous_purchases, review_rating
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["Customer ID"], product_id, season_id,
            subs_id, ship_id, discount_id,
            promo_id, paym_id, freq_id,
            row["Purchase Amount (USD)"], row["Previous Purchases"], row["Review Rating"]
        )
    )
    conn.commit()

# %%
print("PROCESO COMPLETO — datos cargados a SQL Server")

cursor.close()
conn.close()