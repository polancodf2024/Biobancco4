import streamlit as st
import pandas as pd
import paramiko
from pathlib import Path
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuración de los archivos remotos
REMOTE_HOST = "187.217.52.137"
REMOTE_USER = "POLANCO6"
REMOTE_PASSWORD = "tt6plco6"
REMOTE_PORT = 3792
REMOTE_DIR = "/home/POLANCO6"
REMOTE_FILE_XLSX = "respuestas_cuestionario_acumulado.xlsx"
REMOTE_FILE_CSV = "identificaciones.csv"
LOCAL_FILE_XLSX = "respuestas_cuestionario_acumulado.xlsx"
LOCAL_FILE_CSV = "identificaciones.csv"

# Configuración de correo
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "abcdf2024dfabc@gmail.com"
EMAIL_PASSWORD = "hjdd gqaw vvpj hbsy"
NOTIFICATION_EMAIL = "polanco@unam.mx"

# Función para descargar archivos del servidor remoto
def recibir_archivo_remoto(remote_file, local_file):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=REMOTE_PASSWORD)
        sftp = ssh.open_sftp()
        sftp.get(f"{REMOTE_DIR}/{remote_file}", local_file)
        sftp.close()
        ssh.close()
        st.info(f"Archivo {local_file} descargado del servidor remoto.")
    except Exception as e:
        st.error(f"Error al descargar el archivo {remote_file} del servidor remoto.")
        st.error(str(e))

# Función para subir archivos al servidor remoto
def enviar_archivo_remoto(local_file, remote_file):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=REMOTE_PASSWORD)
        sftp = ssh.open_sftp()
        sftp.put(local_file, f"{REMOTE_DIR}/{remote_file}")
        sftp.close()
        ssh.close()
        st.success(f"Archivo {local_file} subido al servidor remoto.")
    except Exception as e:
        st.error(f"Error al subir el archivo {local_file} al servidor remoto.")
        st.error(str(e))

# Función para enviar correos con archivo adjunto
def send_email_with_attachment(email_recipient, subject, body, attachment_path):
    mensaje = MIMEMultipart()
    mensaje['From'] = EMAIL_USER
    mensaje['To'] = email_recipient
    mensaje['Subject'] = subject
    mensaje.attach(MIMEText(body, 'plain'))

    try:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={Path(attachment_path).name}')
            mensaje.attach(part)
    except Exception as e:
        st.error(f"Error al adjuntar el archivo: {e}")

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, email_recipient, mensaje.as_string())

# Solicitar contraseña al inicio
PASSWORD = "tt5plco5"
input_password = st.text_input("Ingresa la contraseña para acceder:", type="password")
if input_password != PASSWORD:
    st.error("Escribe la contraseña correcta, y presiona ENTER.")
    st.stop()

# Sincronización automática al iniciar
try:
    st.info("Sincronizando archivos con el servidor remoto...")
    recibir_archivo_remoto(REMOTE_FILE_XLSX, LOCAL_FILE_XLSX)
    recibir_archivo_remoto(REMOTE_FILE_CSV, LOCAL_FILE_CSV)
except Exception as e:
    st.warning("No se pudo sincronizar los archivos automáticamente.")
    st.warning(str(e))

# Mostrar el logo y título
st.image("escudo_COLOR.jpg", width=150)
st.title("Subir archivos: respuestas_cuestionario_acumulado.xlsx e identificaciones.csv")

# Subida de archivo XLSX
uploaded_xlsx = st.file_uploader("Selecciona el archivo .xlsx para subir y reemplazar el existente", type=["xlsx"])
if uploaded_xlsx is not None:
    try:
        with open(LOCAL_FILE_XLSX, "wb") as f:
            f.write(uploaded_xlsx.getbuffer())

        # Subir al servidor remoto
        enviar_archivo_remoto(LOCAL_FILE_XLSX, REMOTE_FILE_XLSX)

        # Enviar correos al administrador y usuario
        send_email_with_attachment(
            email_recipient=NOTIFICATION_EMAIL,
            subject="Nuevo archivo XLSX subido al servidor",
            body="Se ha subido un nuevo archivo XLSX al servidor.",
            attachment_path=LOCAL_FILE_XLSX
        )
        st.success("Archivo XLSX subido y correo enviado al administrador.")
    except Exception as e:
        st.error("Error al procesar el archivo XLSX.")
        st.error(str(e))

# Subida de archivo CSV
uploaded_csv = st.file_uploader("Selecciona el archivo .csv para subir y reemplazar el existente", type=["csv"])
if uploaded_csv is not None:
    try:
        with open(LOCAL_FILE_CSV, "wb") as f:
            f.write(uploaded_csv.getbuffer())

        # Subir al servidor remoto
        enviar_archivo_remoto(LOCAL_FILE_CSV, REMOTE_FILE_CSV)

        # Enviar correos al administrador y usuario
        send_email_with_attachment(
            email_recipient=NOTIFICATION_EMAIL,
            subject="Nuevo archivo CSV subido al servidor",
            body="Se ha subido un nuevo archivo CSV al servidor.",
            attachment_path=LOCAL_FILE_CSV
        )
        st.success("Archivo CSV subido y correo enviado al administrador.")
    except Exception as e:
        st.error("Error al procesar el archivo CSV.")
        st.error(str(e))

# Título para la sección de descarga
st.title("Descargar archivos: respuestas_cuestionario_acumulado.xlsx e identificaciones.csv")

# Botón para descargar el archivo XLSX
if Path(LOCAL_FILE_XLSX).exists():
    with open(LOCAL_FILE_XLSX, "rb") as file:
        st.download_button(
            label="Descargar respuestas_cuestionario_acumulado.xlsx",
            data=file,
            file_name="respuestas_cuestionario_acumulado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    st.success("Archivo XLSX listo para descargar.")
else:
    st.warning("El archivo XLSX local no existe. Sincroniza primero con el servidor.")

# Botón para descargar el archivo CSV
if Path(LOCAL_FILE_CSV).exists():
    with open(LOCAL_FILE_CSV, "rb") as file:
        st.download_button(
            label="Descargar identificaciones.csv",
            data=file,
            file_name="identificaciones.csv",
            mime="text/csv"
        )
    st.success("Archivo CSV listo para descargar.")
else:
    st.warning("El archivo CSV local no existe. Sincroniza primero con el servidor.")

