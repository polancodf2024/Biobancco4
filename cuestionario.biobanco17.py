import os
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime
from filelock import FileLock


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


# Mostrar el logo
st.image("escudo_COLOR.jpg", width=100)

# Archivo Excel donde se acumularán todas las respuestas
acumulado_excel_file = 'respuestas_cuestionario_acumulado.xlsx'
lock_file = 'acumulado_excel_file.lock'

# Crear un diccionario para almacenar las respuestas
responses = {}

# Título del cuestionario
st.title('Cuestionario Paciente - BioBanco')

# Formulario para todas las preguntas
with st.form(key='cuestionario_form'):
    fecha_entrevista = st.date_input('Fecha de entrevista', value=datetime.now())
    responses['Fecha de entrevista'] = fecha_entrevista.strftime('%d/%m/%Y')

    # Inicio con las preguntas de peso, estatura y otros datos biométricos
    peso = st.number_input('Peso (Kg)', min_value=35.0, max_value=150.0, step=0.1, format="%.1f")
    responses['Peso (Kg)'] = peso

    estatura = st.number_input('Estatura (m)', min_value=1.20, max_value=2.00, step=0.01, format="%.2f")
    responses['Estatura (m)'] = estatura

    if estatura > 0:
        imc = round(peso / (estatura ** 2), 1)
    else:
        imc = 0.0
    responses['Índice de masa corporal (IMC)'] = imc

    responses['Circunferencia de cintura (cm)'] = st.number_input('Circunferencia de cintura (cm)', min_value=50.0, max_value=150.0, step=0.1, format="%.1f")
    responses['Tensión arterial Sistólica (mmHg)'] = st.number_input('Tensión arterial Sistólica (mmHg)', min_value=50, max_value=220, step=1)
    responses['Tensión arterial Diastólica (mmHg)'] = st.number_input('Tensión arterial Diastólica (mmHg)', min_value=40, max_value=130, step=1)
    responses['Frecuencia cardiaca (lpm)'] = st.number_input('Frecuencia cardiaca (lpm)', min_value=40, max_value=120, step=1)

    # Continuación del cuestionario
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

    # Nueva sección de enfermedades familiares
    st.text("¿Tuvo o tiene familiar(es) con alguna de las siguientes enfermedades?")
    enfermedades = [
        'Cardiopatía congénita', 'Angina', 'Valvulopatía', 'Cardiopatía pulmonar',
        'Arritmia cardiaca', 'Coágulos sanguíneos', 'Hipertensión', 'Dislipidemia',
        'Diabetes', 'Insuficiencia cardíaca'
    ]
    familiares = ['Madre', 'Padre', 'Ambos', 'Hermano(a)', 'Ninguno']

    # Diccionario para almacenar respuestas
    enfermedades_respuestas = {enfermedad: {familiar: False for familiar in familiares} for enfermedad in enfermedades}

    for enfermedad in enfermedades:
        st.write(f"**{enfermedad}**")
        cols = st.columns(len(familiares))
        for idx, familiar in enumerate(familiares):
            enfermedades_respuestas[enfermedad][familiar] = cols[idx].checkbox(familiar, key=f"{enfermedad}_{familiar}")

    responses['Familiares con enfermedades específicas'] = enfermedades_respuestas

    # Nueva sección para preguntas con opciones únicas
    st.text("Complete las siguientes preguntas:")
    preguntas = [
        "¿Fuma usted actualmente?",
        "¿En los últimos 3 meses ha tomado alcohol?",
        "¿Tiene exceso de peso?",
        "¿Tiene diabetes?",
        "¿Le han indicado medicamento para la diabetes?",
        "¿Tiene dislipidemia?",
        "¿Le han indicado medicamento para la dislipidemia?",
        "¿Tiene hipertensión?"
    ]

    opciones = ['Sí', 'No', 'No sabe']

    # Diccionario para almacenar respuestas de esta sección
    preguntas_respuestas = {}
    for pregunta in preguntas:
        preguntas_respuestas[pregunta] = st.radio(pregunta, opciones, key=pregunta)

    responses['Preguntas adicionales'] = preguntas_respuestas

    # Preguntas adicionales proporcionadas
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
    # Solo generar el número de muestra al hacer clic en "Guardar Respuestas"
    if 'identificacion' not in st.session_state:
        st.session_state.identificacion = generar_identificacion(prefijo)

    responses['Identificación de la muestra'] = st.session_state.identificacion
    st.write("Identificación de la muestra generada:", st.session_state.identificacion)

    if not num_registro.isdigit():
        st.error('El número de expediente debe ser un valor numérico entre 6 y 10 dígitos.')
    else:
        if '' in responses.values() or any(pd.isna(val) for val in responses.values()):
            st.error('Por favor, responda todas las preguntas antes de guardar.')
        else:
            responses_df = pd.DataFrame([responses])
            individual_excel_file = f'registro_{responses["Núm. registro INCICh"]}.xlsx'
            responses_df.to_excel(individual_excel_file, index=False)

            with FileLock(lock_file):
                if os.path.exists(acumulado_excel_file):
                    existing_data = pd.read_excel(acumulado_excel_file)
                    existing_data = existing_data.loc[:, ~existing_data.columns.duplicated()]
                    new_data = pd.concat([existing_data, responses_df], ignore_index=True)
                    columns_order = ['Fecha de entrevista', 'Nombre del paciente'] + [col for col in new_data.columns if col not in ['Fecha de entrevista', 'Nombre del paciente']]
                    new_data = new_data[columns_order]
                else:
                    new_data = responses_df
                new_data.to_excel(acumulado_excel_file, index=False, engine='openpyxl')
                st.success('Las respuestas han sido guardadas exitosamente.')

if cancel_button:
    st.warning('Para salir sin guardar cierre la aplicación.')
    st.stop()

# Solicitar contraseña para descargar el Excel acumulado
password = st.text_input("Ingrese la contraseña para descargar el archivo:", type="password")
if password == "tt5plco5":
    # Mostrar botón para descargar el archivo solo si la contraseña es correcta
    with open(acumulado_excel_file, 'rb') as file:
        st.download_button(
            label="Descargar archivo Excel acumulado",
            data=file,
            file_name=acumulado_excel_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

