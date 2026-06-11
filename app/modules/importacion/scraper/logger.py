# =============================================================================
# utils/logger.py — Configuración del sistema de logging
# =============================================================================

import re
import logging
from logging.handlers import TimedRotatingFileHandler
import os

class _EmojiFilter(logging.Filter):
    """Elimina emojis y otros caracteres no ASCII del mensaje de log."""
    _RE = re.compile(
        r"["
        r"\U0001F300-\U0001FAFF"  # Misc symbols & pictographs
        r"\U00002700-\U000027BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong
        r"\U0001F0A0-\U0001F0FF"  # Playing cards
        r"\u2600-\u26FF"          # Misc symbols
        r"\u2300-\u23FF"          # Technical symbols
        r"\uFE0F"                 # Variation selector
        r"]",
        flags=re.UNICODE
    )

    def filter(self, record):
        record.msg = self._RE.sub("", str(record.msg)).strip()
        return True


def get_logger(name: str = "webcolegios_bot") -> logging.Logger:
    """
    Crea y devuelve un logger con salida a consola y archivo.
    Usa rotación diaria manteniendo máximo 7 archivos.
    """
    # Directorio y archivo de logs deshabilitados segun requerimientos

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Evita duplicar handlers si el logger ya fue configurado
    if logger.handlers:
        return logger

    emoji_filter = _EmojiFilter()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler consola
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    ch.addFilter(emoji_filter)
    logger.addHandler(ch)

    # Handler archivo rotativo (OPS-02) restaurado segun requerimientos (evitar sobrecarga de BD)
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_live = os.path.join(log_dir, "bot.log")

    lh = TimedRotatingFileHandler(log_file_live, when="midnight", interval=1, backupCount=7, encoding="utf-8")
    lh.setLevel(logging.DEBUG)
    lh.setFormatter(fmt)
    lh.addFilter(emoji_filter)
    logger.addHandler(lh)

    return logger
