from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core.config import settings
from cryptography.fernet import Fernet
import base64
import os

# Generar clave o usar una existente
def get_fernet_key():
    # En producción esto debe venir de settings.SECRET_KEY adaptada a 32 bytes o una variable nueva.
    # Por ahora creamos una llave estática a partir del SECRET_KEY truncado/paneado a 32 bytes para Fernet
    key_material = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
    return base64.urlsafe_b64encode(key_material)

fernet_instance = Fernet(get_fernet_key())

def encriptar_texto(texto: str) -> str:
    if not texto: return texto
    return fernet_instance.encrypt(texto.encode()).decode()

def desencriptar_texto(texto_encriptado: str) -> str:
    if not texto_encriptado: return texto_encriptado
    try:
        return fernet_instance.decrypt(texto_encriptado.encode()).decode()
    except Exception:
        return texto_encriptado # Si falla (por ejemplo, estaba en texto plano antes de la encriptacion), devuelve crudo
def crear_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verificar_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None