from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# Gerar chave privada
chave_privada = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Salvar private_key.pem
with open("private_key.pem", "wb") as f:
    f.write(chave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Gerar e salvar public_key.pem
chave_publica = chave_privada.public_key()
with open("public_key.pem", "wb") as f:
    f.write(chave_publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("Sucesso! Os arquivos private_key.pem e public_key.pem foram criados.")