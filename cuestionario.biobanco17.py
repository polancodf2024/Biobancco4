import sqlite3
import paramiko
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from filelock import FileLock

# Configuración remota
REMOTE_HOST = "187.217.52.137"
REMOTE_USER = "POLANCO6"
REMOTE_PASSWORD = "tt6plco6"
REMOTE_PORT = 3792
REMOTE_DIR = "/home/POLANCO6"
REMOTE_FILE_XLSX = "respuestas_cuestionario_acumulado.xlsx"
LOCAL_FILE_XLSX = "respuestas_cuestionario_acumulado.xlsx"
LOCK_FILE = "acumulado_excel_file.lock"

# Conexión al servidor remoto
def connect_to_remote():
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(REMOTE_HOST, username=REMOTE_USER, password=REMOTE_PASSWORD, port=REMOTE_PORT)
        sftp_client = ssh_client.open_sftp()
        return ssh_client, sftp_client
    except Exception as e:
        st.error(f"Error al conectar al servidor remoto: {e}")
        return None, None

# Descargar archivo remoto
def download_file(sftp_client):
    try:
        sftp_client.get(os.path.join(REMOTE_DIR, REMOTE_FILE_XLSX), LOCAL_FILE_XLSX)
        st.info("Archivo descargado desde el servidor remoto.")
    except Exception as e:
        st.error(f"Error al descargar archivo: {e}")

# Subir archivo remoto
def upload_file(sftp_client):
    try:
        sftp_client.put(LOCAL_FILE_XLSX, os.path.join(REMOTE_DIR, REMOTE_FILE_XLSX))
        st.success("Archivo subido exitosamente al servidor remoto.")
    except Exception as e:
        st.error(f"Error al subir archivo: {e}")

# Cerrar conexión remota
def close_connection(ssh_client, sftp_client):
    if sftp_client:
        sftp_client.close()
    if ssh_client:
        ssh_client.close()
    st.info("Conexión cerrada exitosamente.")


# Conectar a la base de datos SQLite
conn = sqlite3.connect('identificaciones.db')
cursor = conn.cursor()

# Crear la tabla si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS identificaciones (
        id INTEGER PRIMARY KEY,
        prefijo TEXT NOT NULL
    )
''')

def generar_identificacion(prefijo):
    """Genera una nueva identificación consecutiva con el prefijo correspondiente."""
    cursor.execute("INSERT INTO identificaciones (prefijo) VALUES (?)", (prefijo,))
    conn.commit()
    nuevo_id = cursor.lastrowid
    identificacion = f"{prefijo}{nuevo_id:06d}"
    return identificacion


# Generar el cuestionario completo
def generar_cuestionario():
    st.title('Cuestionario Paciente - BioBanco')

    responses = {}
    with st.form(key='cuestionario_form'):
        # Preguntas iniciales ordenadas según imagen
        responses['Fecha de entrevista'] = st.date_input('Fecha de entrevista', value=datetime.now()).strftime('%d/%m/%Y')
        responses['Procedencia del paciente'] = st.selectbox(
            'Procedencia del paciente',
            ['Consulta externa lado A', 'Consulta externa lado B', 'Clínica Arritmias', 'Clínica Coagulación',
             'Clínica Valvulares', 'Clínica Hipertensión', 'Clínica Insuficiencia Cardiaca', 'Donador Control']
        )

        num_registro = st.text_input('Núm. registro INCICh')
        if not num_registro.isdigit():
            st.error('Núm. registro INCICh campo numérico entre 6 y 10 dígitos')
        else:
            responses['Núm. registro INCICh'] = int(num_registro)

        responses['Nombre del paciente'] = st.text_input('Nombre del paciente')
        fecha_nacimiento = st.date_input('Fecha de nacimiento', min_value=datetime(1944, 1, 1), max_value=datetime.now())
        responses['Fecha de nacimiento'] = fecha_nacimiento.strftime('%d/%m/%Y')

        hoy = datetime.now()
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        responses['Edad actual (años)'] = edad

        responses['Género'] = st.selectbox('Género', ['Masculino', 'Femenino', 'Otro'])

        # Preguntas biométricas
        responses['Peso (Kg)'] = st.number_input('Peso (Kg)', min_value=35.0, max_value=150.0, step=0.1)
        responses['Estatura (m)'] = st.number_input('Estatura (m)', min_value=1.20, max_value=2.00, step=0.01)

        if responses['Estatura (m)'] > 0:
            imc = round(responses['Peso (Kg)'] / (responses['Estatura (m)'] ** 2), 1)
        else:
            imc = 0.0
        responses['Índice de masa corporal (IMC)'] = imc


        responses['Circunferencia de cintura (cm)'] = st.number_input('Circunferencia de cintura (cm)', min_value=50.0, max_value=150.0)
        responses['Tensión arterial Sistólica (mmHg)'] = st.number_input('Tensión arterial Sistólica (mmHg)', min_value=50, max_value=220)
        responses['Tensión arterial Diastólica (mmHg)'] = st.number_input('Tensión arterial Diastólica (mmHg)', min_value=40, max_value=130)
        responses['Frecuencia cardiaca (lpm)'] = st.number_input('Frecuencia cardiaca (lpm)', min_value=40, max_value=120)

        responses['Grupo étnico'] = st.selectbox('Grupo étnico', ['Indígena', 'Mestizo', 'Afrodescendiente', 'Otro'])

        # Lugar de nacimiento
        st.text("¿Dónde nació usted y sus familiares?")
        estados_mexico = [
            'Otro', 'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua',
            'Ciudad de Mexico', 'Coahuila', 'Colima', 'Durango', 'Estado de Mexico', 'Guanajuato', 'Guerrero',
            'Hidalgo', 'Jalisco', 'Michoacan', 'Morelos', 'Nayarit', 'Nuevo Leon', 'Oaxaca', 'Puebla', 'Queretaro',
            'Quintana Roo', 'San Luis Potosi', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz',
            'Yucatan', 'Zacatecas'
        ]
#        for familiar in ['abuelo materno', 'abuela materna', 'abuelo paterno', 'abuela paterna', 'padre', 'madre', 'usted']:
#            responses[f"¿Dónde nació su {familiar}?"] = st.selectbox(f"¿Dónde nació su {familiar}?", estados_mexico)

        responses['¿Dónde nació su abuelo materno?'] = st.selectbox('¿Dónde nació su abuelo materno?', estados_mexico)
        responses['¿Dónde nació su abuela materna?'] = st.selectbox('¿Dónde nació su abuela materna?', estados_mexico)
        responses['¿Dónde nació su abuelo paterno?'] = st.selectbox('¿Dónde nació su abuelo paterno?', estados_mexico)
        responses['¿Dónde nació su abuela paterna?'] = st.selectbox('¿Dónde nació su abuela paterna?', estados_mexico)
        responses['¿Dónde nació su padre?'] = st.selectbox('¿Dónde nació su padre?', estados_mexico)
        responses['¿Dónde nació su madre?'] = st.selectbox('¿Dónde nació su madre?', estados_mexico)
        responses['¿Dónde nació usted?'] = st.selectbox('¿Dónde nació usted?', estados_mexico)

        # Enfermedades familiares
        st.text("¿Tuvo o tiene familiar(es) con alguna de las siguientes enfermedades?")
        enfermedades = [
            'Cardiopatía congénita', 'Angina', 'Valvulopatía', 'Cardiopatía pulmonar',
            'Arritmia cardiaca', 'Coágulos sanguíneos', 'Hipertensión', 'Dislipidemia',
            'Diabetes', 'Insuficiencia cardíaca'
        ]
        familiares = ['Madre', 'Padre', 'Ambos', 'Hermano(a)', 'Ninguno']
        enfermedades_respuestas = {enfermedad: {familiar: False for familiar in familiares} for enfermedad in enfermedades}

        for enfermedad in enfermedades:
            st.write(f"**{enfermedad}**")
            cols = st.columns(len(familiares))
            for idx, familiar in enumerate(familiares):
                enfermedades_respuestas[enfermedad][familiar] = cols[idx].checkbox(familiar, key=f"{enfermedad}_{familiar}")
        responses['Familiares con enfermedades específicas'] = enfermedades_respuestas

        # Preguntas adicionales
        st.text("Complete las siguientes preguntas:")
        preguntas = [
            "¿Fuma usted actualmente?",
            "¿En los últimos 3 meses ha tomado alcohol?",
            "¿Tiene exceso de peso?",
            "¿Tiene diabetes?",
            "¿Le han indicado medicamento para la diabetes?",
            "¿Tiene dislipidemia?",
            "¿Le han indicado medicamento para la dislipidemia?",
            "¿Tiene hipertensión?",
            "¿Le han indicado medicamento para la hipertensión?"
        ]
        opciones = ['Sí', 'No', 'No sabe']

        preguntas_respuestas = {}
        for pregunta in preguntas:
            preguntas_respuestas[pregunta] = st.radio(pregunta, opciones, key=pregunta)

        responses['Preguntas adicionales'] = preguntas_respuestas

        responses['¿El paciente firmó el consentimiento informado para participar como donador del Biobanco del INCICh?'] = st.selectbox(
            '¿Firmó el paciente el consentimiento informado?', ['Sí', 'No'], key='firma_consentimiento'
        )

        if responses['Procedencia del paciente'] == 'Donador Control':
            prefijo = 'CB'
        else:
            prefijo = st.selectbox('Si "Procedencia del Paciente = Donador Control", implica que "Identificación de la muestra = CB"', ['PB', 'CB'])

        whatsapp = st.text_input('Proporcione el WhatsApp del donante:')
        if not whatsapp.isdigit() or len(whatsapp) != 10:
            st.error('El número de WhatsApp debe contener exactamente 10 dígitos.')
        else:
            responses['WhatsApp'] = whatsapp

        email = st.text_input('Proporcione el correo electrónico del donante:', value="No proporcionó email")
        responses['Correo electrónico'] = email


        submit_button = st.form_submit_button(label='Guardar Respuestas')
        cancel_button = st.form_submit_button(label='Salir sin Guardar')

    if submit_button:
        if 'identificacion' not in st.session_state:
            st.session_state.identificacion = generar_identificacion(prefijo)

        responses['Identificación de la muestra'] = st.session_state.identificacion
        st.write("Identificación de la muestra generada:", st.session_state.identificacion)
        return responses
    
    return None

# Guardar respuestas localmente
def guardar_respuestas(responses):
    df_respuestas = pd.DataFrame([responses])
    with FileLock(LOCK_FILE):
        if os.path.exists(LOCAL_FILE_XLSX):
            df_existente = pd.read_excel(LOCAL_FILE_XLSX)
            df_final = pd.concat([df_existente, df_respuestas], ignore_index=True)
            df_final = df_final.loc[:, ~df_final.columns.duplicated(keep='first')]  # Eliminar columnas duplicadas
        else:
            df_final = df_respuestas
        df_final.to_excel(LOCAL_FILE_XLSX, index=False, engine='openpyxl')



# Función principal
def main():
    ssh_client, sftp_client = connect_to_remote()
    if ssh_client and sftp_client:
        try:
            download_file(sftp_client)
            responses = generar_cuestionario()
            if responses:
                guardar_respuestas(responses)
                upload_file(sftp_client)
        finally:
            close_connection(ssh_client, sftp_client)
    else:
        st.error("No se pudo conectar al servidor remoto.")

if __name__ == "__main__":
    main()

