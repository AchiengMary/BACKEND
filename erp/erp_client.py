import requests
from requests.auth import HTTPBasicAuth

ERP_BASE_URL = "https://bctest.dayliff.com:7048/BC160/ODataV4/Company(%27KENYA%27)"
USERNAME = "webservice"
PASSWORD = "iqZwQDaYj665WV0aOgbSYFCDHsT9GxSxOUTTwOr5IV0="

def fetch_entity(entity_name: str, entity_id: str = None, top: int = 100, skip: int = 0):
    url = f"{ERP_BASE_URL}/{entity_name}?$top={top}&$skip={skip}"  # Use pagination with top and skip
    if entity_id:
        url += f"({entity_id})"

    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed: {response.status_code} - {response.text}")
