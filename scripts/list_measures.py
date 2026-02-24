import dotenv

dotenv.load_dotenv()
from core.clients.powerbi_client import PowerBIClient

client = PowerBIClient()

query = "select MEASURE_NAME from $SYSTEM.MDSCHEMA_MEASURES"

try:
    res = client.execute_dax(query)
    # The result may be a list of dicts or something similar depending on the execute_dax impl.
    print(res[:5])  # print sample to check format
    # Try finding repasse if it's a list of dicts
    repasse_measures = [x for x in res if "repasse" in str(x).lower()]
    print("Medidas de Repasse encontradas:")
    for m in repasse_measures:
        print(m)
except Exception as e:
    print("FAILED", e)
