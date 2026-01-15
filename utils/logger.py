import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def get_logger(name="automation"):
    """
    Configures and returns a structured logger.
    Logs are saved to 'logs/app.log' and printed to console.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if get_logger is called multiple times
    if logger.handlers:
        return logger
        
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=5*1024*1024, # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
