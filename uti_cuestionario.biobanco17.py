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

# Configuración del archivo remoto
REMOTE_HOST = "187.217.52.137"
REMOTE_USER = "POLANCO6"
REMOTE_PASSWORD = "tt6plco6"
REMOTE_PORT = 3792
REMOTE_DIR = "/home/POLANCO6"
REMOTE_FILE = "respuestas_cuestionario_acumulado.xlsx"
LOCAL_FILE = "respuestas_cuestionario_acumulado.xlsx"

# Configuración de correo
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "abcdf2024dfabc@gmail.com"
EMAIL_PASSWORD = "hjdd gqaw vvpj hbsy"
NOTIFICATION_EMAIL = "polanco@unam.mx"

# Función para descargar el archivo del servidor remoto
def recibir_archivo_remoto():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=REMOTE_PASSWORD)
        sftp = ssh.open_sftp()
        sftp.get(f"{REMOTE_DIR}/{REMOTE_FILE}", LOCAL_FILE)
        sftp.close()
        ssh.close()
        print("Sincronización automática exitosa.")
    except Exception as e:
        st.error("Error al descargar el archivo del servidor remoto.")
        st.error(str(e))

# Función para subir el archivo al servidor remoto
def enviar_archivo_remoto():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=REMOTE_PASSWORD)
        sftp = ssh.open_sftp()
        sftp.put(LOCAL_FILE, f"{REMOTE_DIR}/{REMOTE_FILE}")
        sftp.close()
        ssh.close()
        st.success("Archivo subido al servidor remoto.")
    except Exception as e:
        st.error("Error al subir el archivo al servidor remoto.")
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

# Sincronización automática al iniciar
try:
    st.info("Sincronizando archivo con el servidor remoto...")
    recibir_archivo_remoto()
except Exception as e:
    st.warning("No se pudo sincronizar el archivo automáticamente.")
    st.warning(str(e))

# Solicitar contraseña al inicio
PASSWORD = "tt5plco5"
input_password = st.text_input("Ingresa la contraseña para acceder:", type="password")
if input_password != PASSWORD:
    st.error("Escribe la contraseña correcta, y presiona ENTER.")
    st.stop()

# Mostrar el logo y título
st.image("escudo_COLOR.jpg", width=150)
st.title("Subir el archivo: respuestas_cuestionario_acumulado.xlsx")

# Subida de archivo
uploaded_xlsx = st.file_uploader("Selecciona el archivo para subir y reemplazar el existente", type=["xlsx"])
if uploaded_xlsx is not None:
    try:
        with open(LOCAL_FILE, "wb") as f:
            f.write(uploaded_xlsx.getbuffer())

        # Subir al servidor remoto
        enviar_archivo_remoto()

        # Enviar correos al administrador y usuario
        send_email_with_attachment(
            email_recipient=NOTIFICATION_EMAIL,
            subject="Nuevo archivo subido al servidor",
            body="Se ha subido un nuevo archivo al servidor.",
            attachment_path=LOCAL_FILE
        )
        st.success("Archivo subido y correo enviado al administrador.")
    except Exception as e:
        st.error("Error al procesar el archivo.")
        st.error(str(e))

# Título para la sección de descarga
st.title("Descargar el archivo: respuestas_cuestionario_acumulado.xlsx")

# Botón para descargar el archivo local
if Path(LOCAL_FILE).exists():
    with open(LOCAL_FILE, "rb") as file:
        st.download_button(
            label="Descargar respuestas_cuestionario_acumulado.xlsx",
            data=file,
            file_name="respuestas_cuestionario_acumulado.xlsx",
            mime="text/xlsx"
        )
    st.success("Archivo listo para descargar.")
else:
    st.warning("El archivo local no existe. Sincroniza primero con el servidor.")

