# AURA V2
# Copiar este archivo como app_v2.py

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AURA", page_icon="✨", layout="wide")

conn = sqlite3.connect("stock.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS proveedores(
id INTEGER PRIMARY KEY AUTOINCREMENT,
nombre TEXT UNIQUE)""")

c.execute("""CREATE TABLE IF NOT EXISTS productos(
id INTEGER PRIMARY KEY AUTOINCREMENT,
nombre TEXT,
proveedor_id INTEGER,
precio REAL,
stock INTEGER,
stock_minimo INTEGER,
ultima_modificacion TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS movimientos(
id INTEGER PRIMARY KEY AUTOINCREMENT,
fecha TEXT,
producto_id INTEGER,
tipo TEXT,
cantidad INTEGER)""")

conn.commit()

def obtener_proveedores():
    return pd.read_sql_query("SELECT * FROM proveedores ORDER BY nombre", conn)

def obtener_productos():
    return pd.read_sql_query("""
    SELECT p.id,p.nombre,pr.nombre proveedor,p.precio,p.stock,p.stock_minimo,p.ultima_modificacion
    FROM productos p
    LEFT JOIN proveedores pr ON p.proveedor_id=pr.id
    ORDER BY p.nombre
    """, conn)

st.sidebar.title("✨ AURA")
menu = st.sidebar.radio("Menú",
["Inicio","Productos","Ingreso Mercadería","Ventas","Proveedores","Historial"])

if menu=="Inicio":
    st.title("✨ AURA")
    df=obtener_productos()
    total=len(df)
    stock=int(df["stock"].sum()) if len(df) else 0
    valor=float((df["stock"]*df["precio"]).sum()) if len(df) else 0
    rep=len(df[df["stock"]<=df["stock_minimo"]]) if len(df) else 0
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Productos",total)
    c2.metric("Unidades",stock)
    c3.metric("A reponer",rep)
    c4.metric("Valor stock",f"${valor:,.0f}")

elif menu=="Proveedores":
    st.title("🏢 Proveedores")
    with st.form("prov"):
        nombre=st.text_input("Nuevo proveedor")
        ok=st.form_submit_button("Agregar")
        if ok and nombre:
            c.execute("INSERT OR IGNORE INTO proveedores(nombre) VALUES(?)",(nombre,))
            conn.commit()
            st.success("Proveedor agregado")

    proveedores=obtener_proveedores()
    if len(proveedores):
        sel=st.selectbox("Buscar por proveedor",proveedores["nombre"])
        df=obtener_productos()
        df=df[df["proveedor"]==sel]
        st.metric("Productos",len(df))
        st.metric("Valor stock",f"${(df['stock']*df['precio']).sum():,.0f}")
        st.dataframe(df,use_container_width=True)
        st.divider()

        st.subheader("🗑️ Eliminar proveedor")
        proveedores = obtener_proveedores()

        if len(proveedores):

            proveedor_eliminar = st.selectbox(
           "Proveedor a eliminar",
        proveedores["nombre"],
        key="eliminar_proveedor"
    )

        if st.button("🗑️ Eliminar proveedor"):

           proveedor_id = int(
            proveedores[
                proveedores["nombre"] == proveedor_eliminar
            ]["id"].iloc[0]
        )

           productos_asociados = pd.read_sql_query(
            """
            SELECT *
            FROM productos
            WHERE proveedor_id=?
            """,
            conn,
            params=(proveedor_id,)
        )

           if len(productos_asociados) > 0:

               st.error(
                "No se puede eliminar. Tiene productos asociados."
            )

           else:

            c.execute(
                "DELETE FROM proveedores WHERE id=?",
                (proveedor_id,)
            )

            conn.commit()

            st.success("Proveedor eliminado")

            st.rerun()
            
elif menu=="Productos":
    st.title("📦 Productos")
    proveedores=obtener_proveedores()

    with st.form("p"):
        nombre=st.text_input("Nombre")
        if len(proveedores):
            prov=st.selectbox("Proveedor",proveedores["nombre"])
        else:
            prov=None
            st.warning("Primero cargá proveedores")
        precio=st.number_input("Precio",0.0)
        stock=st.number_input("Stock inicial",0,step=1)
        minimo=st.number_input("Stock mínimo",0,step=1)
        ok=st.form_submit_button("Guardar")

        if ok and prov:
            pid=int(proveedores[proveedores["nombre"]==prov]["id"].iloc[0])
            c.execute("INSERT INTO productos(nombre,proveedor_id,precio,stock,stock_minimo,ultima_modificacion) VALUES(?,?,?,?,?,?)",
            (nombre,pid,precio,stock,minimo,datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()
            st.success("Guardado")

        df=obtener_productos()
        buscar=st.text_input("🔎 Buscar producto")
        if buscar:
          df=df[df["nombre"].str.contains(buscar,case=False,na=False)]
          st.dataframe(df,use_container_width=True)
          st.divider()

    st.subheader("🗑️ Eliminar producto")
    df = obtener_productos()

    if len(df):
              producto_eliminar = st.selectbox(
        "Producto a eliminar",
        df["nombre"],
        key="eliminar_producto"
    )

    if st.button("🗑️ Eliminar producto"):

        producto_id = int(
            df[df["nombre"] == producto_eliminar]["id"].iloc[0]
        )

        c.execute(
            "DELETE FROM movimientos WHERE producto_id=?",
            (producto_id,)
        )

        c.execute(
            "DELETE FROM productos WHERE id=?",
            (producto_id,)
        )

        conn.commit()

        st.success("Producto eliminado")

        st.rerun()
        
elif menu=="Ventas":

    st.title("⬇️ Ventas")

    df = obtener_productos()

    if len(df) == 0:

        st.warning("No hay productos cargados.")

    else:

        if "carrito" not in st.session_state:
            st.session_state.carrito = []

        col1, col2 = st.columns(2)

        with col1:
            producto = st.selectbox(
                "Producto",
                df["nombre"]
            )

        with col2:
            cantidad = st.number_input(
                "Cantidad",
                min_value=1,
                step=1
            )

        if st.button("➕ Agregar al carrito"):

            fila = df[df["nombre"] == producto].iloc[0]

            precio = float(fila["precio"])

            st.session_state.carrito.append({
                "producto": producto,
                "cantidad": cantidad,
                "precio": precio,
                "subtotal": precio * cantidad
            })

            st.success("Producto agregado al carrito")

        st.divider()

        st.subheader("🛒 Venta actual")

        if len(st.session_state.carrito) > 0:

            carrito_df = pd.DataFrame(
                st.session_state.carrito
            )

            st.dataframe(
                carrito_df,
                use_container_width=True,
                hide_index=True
            )

            total = carrito_df["subtotal"].sum()

            st.metric(
                "💰 Total a cobrar",
                f"${total:,.0f}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button("🗑️ Vaciar carrito"):

                    st.session_state.carrito = []

                    st.rerun()

            with col2:

                if st.button("✅ Confirmar venta"):

                    error_stock = False

                    for item in st.session_state.carrito:

                        fila = df[
                            df["nombre"] == item["producto"]
                        ].iloc[0]

                        if item["cantidad"] > int(fila["stock"]):

                            st.error(
                                f"Stock insuficiente para {item['producto']}"
                            )

                            error_stock = True
                            break

                    if not error_stock:

                        fecha = datetime.now().strftime(
                            "%d/%m/%Y %H:%M"
                        )

                        for item in st.session_state.carrito:

                            fila = df[
                                df["nombre"] == item["producto"]
                            ].iloc[0]

                            nuevo_stock = (
                                int(fila["stock"])
                                - item["cantidad"]
                            )

                            c.execute("""
                            UPDATE productos
                            SET stock=?,
                                ultima_modificacion=?
                            WHERE id=?
                            """,
                            (
                                nuevo_stock,
                                fecha,
                                int(fila["id"])
                            ))

                            c.execute("""
                            INSERT INTO movimientos(
                                fecha,
                                producto_id,
                                tipo,
                                cantidad
                            )
                            VALUES(?,?,?,?)
                            """,
                            (
                                fecha,
                                int(fila["id"]),
                                "VENTA",
                                item["cantidad"]
                            ))

                        conn.commit()

                        st.session_state.carrito = []

                        st.success(
                            f"Venta registrada. Total cobrado: ${total:,.0f}"
                        )

                        st.rerun()

        else:

            st.info(
                "Todavía no agregaste productos al carrito."
            )
elif menu=="Ingreso Mercadería":
    st.title("⬆️ Ingreso")
    df=obtener_productos()
    if len(df):
        producto=st.selectbox("Producto",df["nombre"])
        cant=st.number_input("Cantidad",1,step=1)
        if st.button("Ingresar stock"):
            fila=df[df["nombre"]==producto].iloc[0]
            nuevo=int(fila["stock"])+cant
            c.execute("UPDATE productos SET stock=?,ultima_modificacion=? WHERE id=?",
            (nuevo,datetime.now().strftime("%d/%m/%Y %H:%M"),int(fila["id"])))
            c.execute("INSERT INTO movimientos(fecha,producto_id,tipo,cantidad) VALUES(?,?,?,?)",
            (datetime.now().strftime("%d/%m/%Y %H:%M"),int(fila["id"]),"INGRESO",cant))
            conn.commit()
            st.success(f"Stock actual: {nuevo}")



elif menu=="Historial":
    st.title("📜 Historial")
        
    hist = pd.read_sql_query("""
SELECT
    m.id,
    m.fecha,
    p.nombre producto,
    m.tipo,
    m.cantidad,
    p.id producto_id
FROM movimientos m
LEFT JOIN productos p
ON m.producto_id = p.id
ORDER BY m.id DESC
""", conn)

    st.dataframe(hist, use_container_width=True)
    st.divider()

    st.subheader("↩️ Anular venta")

    ventas = hist[hist["tipo"] == "VENTA"]

    if len(ventas):

      venta_id = st.selectbox(
        "Movimiento",
        ventas["id"]
    )

    if st.button("↩️ Anular venta"):

        venta = ventas[
            ventas["id"] == venta_id
        ].iloc[0]

        producto_id = int(venta["producto_id"])
        cantidad = int(venta["cantidad"])

        c.execute("""
        UPDATE productos
        SET stock = stock + ?
        WHERE id=?
        """,
        (
            cantidad,
            producto_id
        ))

        c.execute(
            "DELETE FROM movimientos WHERE id=?",
            (int(venta_id),)
        )

        conn.commit()

        st.success(
            f"Venta anulada. Se devolvieron {cantidad} unidades al stock."
        )

        st.rerun()