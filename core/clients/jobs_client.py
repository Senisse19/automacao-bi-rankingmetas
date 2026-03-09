import requests
import requests.adapters
from urllib3.util.retry import Retry

from config import NEXUS_CONFIG
from utils.logger import get_logger

logger = get_logger("jobs_client")


class JobsClient:
    def __init__(self):
        self.api_url = NEXUS_CONFIG["api_url"]
        self.token = NEXUS_CONFIG["token"]
        self.headers = {"Content-Type": "application/json", "X-API-KEY": self.token}

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries=retries))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))

    def fetch_all_jobs(self):
        """Fetches all jobs from the Data Lake."""
        return self.fetch_all("/jobs/")

    def fetch_all(self, endpoint):
        """Generic fetch all with pagination."""
        all_items = []
        page = 1
        limit = 500

        # Ensure endpoint starts with slash but base url doesn't have double slash issues
        # api_url usually doesn't have trailing slash.
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        url = f"{self.api_url}{endpoint}"

        logger.info(f"Fetching data from: {url}")

        while True:
            try:
                params = {"page": page, "limit": limit}

                # Para POST endpoints que se comportam como GET (alguns casos legados ou específicos)
                # Mas por padrao vamos de GET. Se precisar de POST, o metodo deve receber argumento.
                resp = self.session.get(url, headers=self.headers, params=params, timeout=60)

                if resp.status_code != 200:
                    logger.error(f"Failed to fetch page {page}: {resp.status_code} - {resp.text[:100]}")
                    break

                data = resp.json()
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("results") or data.get("data") or []

                if not items:
                    break

                all_items.extend(items)
                logger.info(f"Page {page}: Fetched {len(items)} items. Total so far: {len(all_items)}")

                if len(items) < limit:
                    break

                page += 1
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break

        return all_items
