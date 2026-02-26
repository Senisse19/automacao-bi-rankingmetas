import uvicorn
import argparse
from dotenv import load_dotenv

load_dotenv()
from utils.logger import get_logger

logger = get_logger("api_server")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inicia a API do Studio Automation Core")
    parser.add_argument("--host", default="0.0.0.0", help="Host da API")
    parser.add_argument("--port", type=int, default=8000, help="Porta da API")
    parser.add_argument("--reload", action="store_true", help="Habilita reload automático")
    args = parser.parse_args()

    logger.info(f"Iniciando API no endereço http://{args.host}:{args.port}")
    uvicorn.run("core.api.main:app", host=args.host, port=args.port, reload=args.reload)
