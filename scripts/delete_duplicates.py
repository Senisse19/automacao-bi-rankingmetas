import requests
import pandas as pd
from core.services.supabase_service import SupabaseService


def clean_duplicates():
    print("Fetching all accounts...")
    svc = SupabaseService()
    url = svc.url
    headers = svc.headers

    all_rows = []
    offset = 0
    limit = 1000
    while True:
        endpoint = (
            f"{url.rstrip('/')}/rest/v1/nexus_contas_receber?select=id,codigo,updated_at&offset={offset}&limit={limit}"
        )
        resp = requests.get(endpoint, headers=headers)

        if resp.status_code >= 400:
            print(f"Error fetching data: {resp.text}")
            break

        data = resp.json()
        if not data:
            break
        all_rows.extend(data)
        if len(data) < limit:
            break
        offset += limit

    df = pd.DataFrame(all_rows)
    print(f"Total rows fetched: {len(df)}")

    if not df.empty:
        df = df.sort_values(by="updated_at", ascending=True)
        to_delete = df[df.duplicated(subset=["codigo"], keep="last")]

        print(f"Found {len(to_delete)} duplicate rows to delete.")

        ids_to_delete = to_delete["id"].tolist()

        if len(ids_to_delete) > 0:
            batch_size = 100
            for i in range(0, len(ids_to_delete), batch_size):
                batch_ids = ids_to_delete[i : i + batch_size]
                id_list_str = ",".join(map(str, batch_ids))

                del_endpoint = f"{url.rstrip('/')}/rest/v1/nexus_contas_receber?id=in.({id_list_str})"
                del_resp = requests.delete(del_endpoint, headers=headers)

                if del_resp.status_code >= 400:
                    print(f"Failed to delete batch: {del_resp.text}")
                else:
                    print(f"Deleted batch {i // batch_size + 1}")

            print("Done cleaning duplicates.")


if __name__ == "__main__":
    clean_duplicates()
