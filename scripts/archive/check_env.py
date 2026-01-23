import os
from dotenv import load_dotenv

load_dotenv()

print(f"NEXUS_API_URL: {os.getenv('NEXUS_API_URL')}")
print(f"UNIDADES_API_URL: {os.getenv('UNIDADES_API_URL')}")
