import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class _JSONFormatter(logging.Formatter):
    """
    Formata log records como JSON de uma linha — ideal para ferramentas de
    agregação (Loki, Datadog, CloudWatch) e grep estruturado.

    Exemplo de saída:
        {"timestamp": "2026-03-10T14:32:01", "level": "INFO",
         "logger": "scheduler", "message": "Job iniciado"}
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


# Formatter legível para console (sem mudanças na experiência de dev)
_CONSOLE_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str = "automation") -> logging.Logger:
    """
    Retorna um logger configurado com:
    - Arquivo rotativo (JSON, 5 MB, 3 backups) — estruturado para ferramentas de log
    - Console (texto legível) — para desenvolvimento e Docker logs
    """
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Evita adicionar handlers duplicados se get_logger for chamado várias vezes
    if logger.handlers:
        return logger

    # ── Handler de arquivo: JSON rotativo ───────────────────────────────────
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(_JSONFormatter())

    # ── Handler de console: texto legível ───────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_CONSOLE_FORMATTER)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
