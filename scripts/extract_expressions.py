import dotenv

dotenv.load_dotenv()
from core.clients.powerbi_client import PowerBIClient

client = PowerBIClient()
query = "select MEASURE_NAME, EXPRESSION from $SYSTEM.MDSCHEMA_MEASURES where MEASURE_NAME in ('total_repasse', 'Valor_OutrasReceitas', 'Valor_InterCompany', 'Valor_Corporate_Repasse')"

try:
    res = client.execute_dax(query)
    for row in res:
        print(row.get("MEASURE_NAME"))
        print(row.get("EXPRESSION"))
        print("-" * 40)
except Exception as e:
    print("FAILED", e)
