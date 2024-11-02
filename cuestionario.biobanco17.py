import sqlite3
import streamlit as st
import pandas as pd
import os
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

# Lista de estados de la República Mexicana
estados_mexico = [
    'Otro', 'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 
    'Ciudad de Mexico', 'Coahuila', 'Colima', 'Durango', 'Estado de Mexico', 'Guanajuato', 'Guerrero', 
    'Hidalgo', 'Jalisco', 'Michoacan', 'Morelos', 'Nayarit', 'Nuevo Leon', 'Oaxaca', 'Puebla', 'Queretaro', 
    'Quintana Roo', 'San Luis Potosi', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 
    'Yucatan', 'Zacatecas'
]

# Crear un diccionario para almacenar las respuestas
responses = {}

# Título del cuestionario
st.title('Cuestionario Paciente - BioBanco')

# Formulario para todas las preguntas
with st.form(key='cuestionario_form'):
    fecha_entrevista = st.date_input('Fecha de entrevista', value=datetime.now())
    responses['Fecha de entrevista'] = fecha_entrevista.strftime('%d/%m/%Y')

    responses['Procedencia del paciente'] = st.selectbox(
        'Procedencia del paciente', 
        ['Consulta externa lado A', 'Consulta externa lado B', 'Clínica Arritmias', 'Clínica Coagulación', 
         'Clínica Valvulares', 'Clínica Hipertensión', 'Donador Control']
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

    responses['Grupo étnico al que pertenece.'] = st.selectbox('Grupo étnico al que pertenece.', ['Otro', 'Mestizo', 'Pueblo indígena', 'Caucásico', 'Afrodescendiente'])
    responses['¿Dónde nació su abuelo materno?'] = st.selectbox('¿Dónde nació su abuelo materno?', estados_mexico)
    responses['¿Dónde nació su abuela materna?'] = st.selectbox('¿Dónde nació su abuela materna?', estados_mexico)
    responses['¿Dónde nació su abuelo paterno?'] = st.selectbox('¿Dónde nació su abuelo paterno?', estados_mexico)
    responses['¿Dónde nació su abuela paterna?'] = st.selectbox('¿Dónde nació su abuela paterna?', estados_mexico)
    responses['¿Dónde nació su padre?'] = st.selectbox('¿Dónde nació su padre?', estados_mexico)
    responses['¿Dónde nació su madre?'] = st.selectbox('¿Dónde nació su madre?', estados_mexico)
    responses['¿Dónde nació usted?'] = st.selectbox('¿Dónde nació usted?', estados_mexico)
    
    responses['¿Tuvo o tiene familiar con alguna de las siguientes enfermedades?'] = st.selectbox(
        '¿Tuvo o tiene familiar con alguna de las siguientes enfermedades?', 
        ['Ninguna', 'Angina inestable', 'Angina estable', 'Cardiopatía congénita', 'Valvulopatía', 
         'Cardiopatía pulmonar', 'Arritmia cardiaca', 'Coágulos sanguíneos', 'Hipertensión sistémica', 
         'Dislipidemia', 'Diabetes', 'Hiperuricemia', 'Tabaquismo', 'Sobrepeso', 'Cardiopatía Isquémica']
    )
    
    responses['¿Quién?'] = st.selectbox('¿Quién?', ['Madre', 'Padre', 'Ambos', 'Hermano(a)', 'Ninguno'])
    responses['¿Fuma actualmente?'] = st.selectbox('¿Fuma actualmente?', ['Sí', 'No', 'No sabe'])
    responses['En los últimos 3 meses ¿ha consumido alguna bebida que contenga alcohol?'] = st.selectbox(
        'En los últimos 3 meses ¿ha consumido alguna bebida que contenga alcohol?', ['Sí', 'No', 'No sabe']
    )

    responses['¿El paciente tiene exceso de peso?'] = 'Sí' if imc > 25 else 'No'
    responses['¿El paciente tiene diabetes?'] = st.selectbox('¿El paciente tiene diabetes?', ['Sí', 'No', 'No sabe'])
    responses['¿Le han indicado medicamento(s) para controlar su diabetes?'] = st.selectbox(
        '¿Le han indicado medicamento(s) para controlar su diabetes?', ['Sí', 'No', 'No sabe']
    )

    responses['¿El paciente tiene dislipidemia?'] = st.selectbox('¿El paciente tiene dislipidemia?', ['Sí', 'No', 'No sabe'])
    responses['¿Toma usted algún medicamento para los lípidos?'] = st.selectbox(
        '¿Toma usted algún medicamento para los lípidos?', ['Sí', 'No', 'No sabe'], key='medicamento_lipicos'
    )
    responses['¿El paciente tiene hipertensión arterial?'] = st.selectbox('¿El paciente tiene hipertensión arterial?', ['Sí', 'No', 'No sabe'])
    responses['¿Le han indicado medicamentos para controlar la presión?'] = st.selectbox(
        '¿Le han indicado medicamentos para controlar la presión?', ['Sí', 'No', 'No sabe'], key='medicamentos_presion'
    )
    responses['¿El paciente firmó el consentimiento informado para participar como donador del Biobanco del INCICh?'] = st.selectbox(
        '¿Firmó el paciente el consentimiento informado?', ['Sí', 'No'], key='firma_consentimiento'
    )

    if responses['Procedencia del paciente'] == 'Donador Control':
        prefijo = 'CB'
    else:
        prefijo = st.selectbox('Si "Procedencia del Paciente = Donador Control", implica que "Identificación de la muestra = CB"', ['PB', 'CB'])

    # Pregunta para el número de WhatsApp
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

