import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional

# Configurações do seu servidor SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USUARIO = "ricardomachadolopes@gmail.com"
EMAIL_SENHA = "vrgd vhly deji kjyt"

# Lista de destinatários
DESTINATARIOS = ["eldovane@gmail.com", "ricardomachadolopes@gmail.com"]


def enviar_alerta(assunto: str, mensagem: str, anexo: dict = None, to: Optional[List[str]] = None):
    """
    Envia um alerta por e-mail.

    :param assunto: assunto do e-mail
    :param mensagem: corpo da mensagem
    :param anexo: dicionário opcional {'nome_arquivo': str, 'conteudo': str} para anexar arquivo
    :param to: lista opcional de destinatários (se não informado, usa DESTINATARIOS padrão)
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USUARIO
        msg["To"] = ", ".join(to or DESTINATARIOS)
        msg["Subject"] = assunto

        # Corpo da mensagem
        msg.attach(MIMEText(mensagem, "plain"))

        # Adiciona anexo somente se fornecido
        if anexo:
            part = MIMEApplication(anexo["conteudo"].encode("utf-8"), Name=anexo["nome_arquivo"])
            part['Content-Disposition'] = f'attachment; filename="{anexo["nome_arquivo"]}"'
            msg.attach(part)

        # Envia e-mail
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USUARIO, EMAIL_SENHA)
            server.sendmail(EMAIL_USUARIO, to or DESTINATARIOS, msg.as_string())

        print(f"📧 Alerta enviado: {assunto}")

    except Exception as e:
        print(f"❌ Falha ao enviar alerta: {e}")