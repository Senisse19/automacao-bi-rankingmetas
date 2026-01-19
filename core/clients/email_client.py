import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from utils.logger import get_logger

logger = get_logger("email_client")

class EmailClient:
    def __init__(self, config):
        self.smtp_server = config.get("smtp_server", "smtp.office365.com")
        self.smtp_port = int(config.get("smtp_port", 587))
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.sender_email = config.get("sender_email", "")
        
    def send_email(self, recipients, subject, body, attachment_path=None):
        """
        Envia um email para uma lista de destinatários.
        
        Args:
            recipients (list): Lista de emails de destino
            subject (str): Assunto do email
            body (str): Corpo do email
            attachment_path (str, optional): Caminho para arquivo anexo
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        if not recipients:
            logger.warning("   [Email] Nenhum destinatário definido.")
            return False
            
        if not self.username or not self.password:
            logger.warning("   [Email] Credenciais não configuradas. Pulando envio.")
            return False

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if attachment_path:
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(
                        f.read(),
                        Name=os.path.basename(attachment_path)
                    )
                # After the file is closed
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
            except Exception as e:
                logger.error(f"   [Email] Erro ao anexar arquivo: {e}")
                return False

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.sender_email, recipients, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            logger.error(f"   [Email] Erro ao enviar email: {e}")
            return False
