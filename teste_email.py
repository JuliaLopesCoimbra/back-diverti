import smtplib

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "n1appservicos@gmail.com"
SMTP_PASS = "qyem qrpo lgmk ilxs"  # As aspas são obrigatórias

try:
    print("Conectando ao Gmail...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    server.starttls()
    print("Tentando fazer login...")
    server.login(SMTP_USER, SMTP_PASS)
    print("SUCESSO: O Gmail aceitou a conexão e o login!")
    server.quit()
except Exception as e:
    print(f"ERRO: {e}")
