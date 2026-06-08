import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from sqlmodel import select

from app.core.database import DatabaseSession
from app.models.config import EmailConfig
from app.settings import settings
from app.settings.log import logger


async def send_email(receiver: str, subject: str, body: str):
    """异步发送邮件"""
    if not settings.FEATURE_EMAIL:
        logger.sysLogger.warning("邮件功能已关闭（FEATURE_EMAIL=False）")
        return False

    with DatabaseSession() as session:
        config = session.exec(select(EmailConfig)).first()

    if not config or not config.host:
        logger.sysLogger.error("邮件配置未设置")
        return False

    message = MIMEMultipart()
    message["From"] = formataddr(pair=(config.sender, config.username))
    message["To"] = receiver
    message["Subject"] = Header(subject, "utf-8").encode()
    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(config.host, config.port) as smtp_server:
            if config.use_tls:
                smtp_server.starttls()
            smtp_server.login(config.username, config.password)
            smtp_server.sendmail(config.username, receiver, message.as_string())
        logger.sysLogger.info(f"发送邮件给{receiver}成功")
        return True
    except Exception as e:
        logger.sysLogger.error(f"发送邮件给{receiver}失败：{e}")
        return False
