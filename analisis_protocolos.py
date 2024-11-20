import streamlit as st
import pandas as pd

# URL fija del archivo en línea
CSV_URL = "https://raw.githubusercontent.com/polancodf2024/Protocolos/main/registro_protocolos.csv"

# Título de la aplicación
st.title("Análisis del archivo registro_protocolos.csv")

try:
    # Leer el archivo CSV desde la URL
    datos = pd.read_csv(CSV_URL)
    
    # Mostrar el contenido del archivo
    st.write("### Contenido del archivo:")
    st.dataframe(datos)

    # Análisis del archivo
    if 'Estado' in datos.columns:
        # Contar las ocurrencias de "Activo" y "Terminado" en la columna 'Estado'
        conteo_activo = datos['Estado'].str.count('Activo').sum()
        conteo_terminado = datos['Estado'].str.count('Terminado').sum()

        # Mostrar los resultados
        st.write("### Análisis del archivo:")
        st.write(f"- **Registros con estado 'Activo'**: {conteo_activo}")
        st.write(f"- **Registros con estado 'Terminado'**: {conteo_terminado}")
    else:
        st.error("El archivo no contiene la columna 'Estado'.")

except Exception as e:
    # Mostrar error si no se puede cargar el archivo
    st.error(f"Error al cargar o procesar el archivo: {e}")

