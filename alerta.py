import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurações do seu servidor SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USUARIO = "ricardomachadolopes@gmail.com"
EMAIL_SENHA = "Ta280387"


# Lista de destinatários
DESTINATARIOS = ["eldovane@gmail.com", "ricardomachadolopes@gmail.com"]

def enviar_alerta(assunto: str, mensagem: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USUARIO
        msg["To"] = ", ".join(DESTINATARIOS)
        msg["Subject"] = assunto

        msg.attach(MIMEText(mensagem, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USUARIO, EMAIL_SENHA)
            server.sendmail(EMAIL_USUARIO, DESTINATARIOS, msg.as_string())
        print(f"📧 Alerta enviado: {assunto}")
    except Exception as e:
        print(f"❌ Falha ao enviar alerta: {e}")
