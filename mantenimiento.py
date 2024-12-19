import sqlite3
import streamlit as st

# Conectar a la base de datos
def conectar_db():
    conn = sqlite3.connect('identificaciones.db')
    return conn

# Crear tabla si no existe
def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS identificaciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prefijo TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Mostrar registros en la tabla identificaciones
def mostrar_identificaciones():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM identificaciones")
    registros = cursor.fetchall()
    conn.close()
    return registros

# Agregar un nuevo registro
def agregar_identificacion(prefijo):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO identificaciones (prefijo) VALUES (?)", (prefijo,))
    conn.commit()
    conn.close()

# Actualizar un registro
def actualizar_identificacion(id_actualizar, nuevo_prefijo):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE identificaciones SET prefijo = ? WHERE id = ?", (nuevo_prefijo, id_actualizar))
    conn.commit()
    conn.close()

# Borrar un registro
def borrar_identificacion(id_borrar):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM identificaciones WHERE id = ?", (id_borrar,))
    conn.commit()
    conn.close()

# Interfaz de usuario con Streamlit
st.title("Gestión de Identificaciones")
inicializar_db()

menu = ["Ver registros", "Añadir registro", "Actualizar registro", "Borrar registro"]
opcion = st.sidebar.selectbox("Menú", menu)

if opcion == "Ver registros":
    st.subheader("Registros existentes")
    registros = mostrar_identificaciones()
    if registros:
        for registro in registros:
            st.write(f"ID: {registro[0]}, Prefijo: {registro[1]}")
    else:
        st.write("No hay registros en la base de datos.")

elif opcion == "Añadir registro":
    st.subheader("Añadir un nuevo registro")
    nuevo_prefijo = st.text_input("Ingrese el prefijo:")
    if st.button("Añadir"):
        if nuevo_prefijo:
            agregar_identificacion(nuevo_prefijo)
            st.success("Registro añadido exitosamente.")
        else:
            st.error("El prefijo no puede estar vacío.")

elif opcion == "Actualizar registro":
    st.subheader("Actualizar un registro existente")
    registros = mostrar_identificaciones()
    if registros:
        id_actualizar = st.selectbox("Seleccione el ID del registro a actualizar:", [registro[0] for registro in registros])
        nuevo_prefijo = st.text_input("Ingrese el nuevo prefijo:")
        if st.button("Actualizar"):
            if nuevo_prefijo:
                actualizar_identificacion(id_actualizar, nuevo_prefijo)
                st.success("Registro actualizado exitosamente.")
            else:
                st.error("El prefijo no puede estar vacío.")
    else:
        st.write("No hay registros disponibles para actualizar.")

elif opcion == "Borrar registro":
    st.subheader("Borrar un registro existente")
    registros = mostrar_identificaciones()
    if registros:
        id_borrar = st.selectbox("Seleccione el ID del registro a borrar:", [registro[0] for registro in registros])
        if st.button("Borrar"):
            borrar_identificacion(id_borrar)
            st.success("Registro borrado exitosamente.")
    else:
        st.write("No hay registros disponibles para borrar.")

