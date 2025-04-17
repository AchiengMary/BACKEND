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


def fetch_product_by_number(product_number: str):

    # URL encode the product number as it may contain special characters
    import urllib.parse
    encoded_number = urllib.parse.quote(product_number)
    
    # Build URL with filter for exact product number
    url = f"{ERP_BASE_URL}/ItemsAPI?$filter=No eq '{encoded_number}'"
    
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        data = response.json()
        # If there's no product found, return empty dict or appropriate message
        if not data.get('value') or len(data['value']) == 0:
            return {"message": "No product found with the given number", "data": None}
        return data
    else:
        raise Exception(f"Failed: {response.status_code} - {response.text}")