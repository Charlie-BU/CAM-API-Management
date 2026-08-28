import os
import ssl
import certifi
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("MAIL_SERVER")
SMTP_PORT = int(os.getenv("MAIL_PORT", 465))
SMTP_USER = os.getenv("MAIL_USERNAME")
SMTP_PASSWORD = os.getenv("MAIL_PASSWORD")
SMTP_SENDER = os.getenv("MAIL_DEFAULT_SENDER")


async def send_email(
    to_email: list[str], subject: str, content: str, is_html: bool = False
) -> dict:
    """
    异步发送邮件工具函数
    :param to_email: 收件人邮箱列表
    :param subject: 邮件主题
    :param content: 邮件内容
    :param is_html: 是否为HTML格式
    :return: 发送结果字典
    """
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD]):
        print("Error: SMTP configuration missing")
        return {"status": -1, "message": "SMTP config missing"}

    if not to_email:
        return {"status": -1, "message": "No recipients provided"}

    # 构建邮件对象
    message = MIMEMultipart()
    message["From"] = SMTP_SENDER
    message["To"] = ", ".join(
        to_email
    )  # 邮件头中的To字段，展示给用户看，通常用逗号连接
    message["Subject"] = subject

    # 设置邮件正文
    msg_type = "html" if is_html else "plain"
    message.attach(MIMEText(content, msg_type, "utf-8"))

    try:
        # 创建 SSL 上下文，使用 certifi 提供的 CA 证书
        context = ssl.create_default_context(cafile=certifi.where())
        
        # 异步连接并发送
        await aiosmtplib.send(
            message,
            recipients=to_email,  # 显式指定收件人列表
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=True,  # 如果端口是 465 通常需要 True，587 通常用 start_tls
            tls_context=context, # 显式传入 SSL 上下文
        )
        return {"status": 200, "message": "Email sent successfully"}
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return {"status": -2, "message": f"Failed to send email: {str(e)}"}
