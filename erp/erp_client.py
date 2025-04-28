import datetime
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

load_dotenv()

ERP_BASE_URL = os.getenv("ERP_BASE_URL")
USERNAME = os.getenv("ERP_USERNAME")
PASSWORD = os.getenv("ERP_PASSWORD")

def fetch_entity(entity_name: str, entity_id: str = None, top: int = 100, skip: int = 0):
    url = f"{ERP_BASE_URL}/{entity_name}?$top={top}&$skip={skip}"  # Use pagination with top and skip
    if entity_id:
        url += f"({entity_id})"

    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed: {response.status_code} - {response.text}")
    
def fetch_customer_by_phone_number(Phone_No: str):

    # URL encode the phone number as it may contain special characters.
    import urllib.parse
    encoded_number = urllib.parse.quote(Phone_No)
    
    # Build URL with filter for exact product number
    url = f"{ERP_BASE_URL}/Customer_Card?$filter=Phone_No eq '{encoded_number}'"
    
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        data = response.json()
        # If there's no customer found, return empty dict or appropriate message
        if not data.get('value') or len(data['value']) == 0:
            return {"message": "No customer found with the given number", "data": None}
        return data
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
        print(f"Fetched product data: {data}")
        # If there's no product found, return empty dict or appropriate message
        if not data.get('value') or len(data['value']) == 0:
            return {"message": "No product found with the given number", "data": None}
        return data
    else:
        raise Exception(f"Failed: {response.status_code} - {response.text}")
    
def calculate_price_with_tax(product_data):

    unit_price = product_data.get('Unit_Price', 0)
    vat_group = product_data.get('VAT_Prod_Posting_Group', '')
    
    # Set tax rate based on VAT_Prod_Posting_Group
    tax_rate = 0
    if vat_group == 'VAT16':
        tax_rate = 0.16  # 16% tax
    elif vat_group == 'VAT8':
        tax_rate = 0.08  # 8% tax
   
    
    # Calculate tax amount and total price
    tax_amount = unit_price * tax_rate
    total_price = unit_price + tax_amount
    
    return {
        'unit_price': unit_price,
        'tax_rate': tax_rate * 100,  # Convert to percentage
        'tax_amount': tax_amount,
        'total_price': total_price
    }

def get_product_quotation(product_number: str, phone_number: str = None, name: str = None):
    # Validate that either phone_number or name is provided
    if not phone_number and not name:
        return {
            "status": "error",
            "message": "Either phone number or name must be provided",
            "data": None
        }
    
    # Fetch customer information
    customer_data = None
    if phone_number:
        customer_response = fetch_customer_by_field("Phone_No", phone_number)
        if customer_response.get('value'):
            customer_data = customer_response['value'][0]
    
    if not customer_data and name:
        customer_response = fetch_customer_by_field("Name", name)
        if customer_response.get('value'):
            customer_data = customer_response['value'][0]
    
    # Fetch product from ERP
    product_response = fetch_product_by_number(product_number)
    
    # Check if product was found
    if not product_response.get('value') or len(product_response['value']) == 0:
        return {
            "status": "error",
            "message": f"Product with number {product_number} not found",
            "data": None
        }
    
    # Extract product data
    product_data = product_response['value'][0]
    
    # Calculate prices
    unit_price = product_data.get('Unit_Price', 0)
    installation_fittings = 15000  # Default value
    installation_labor = 20000     # Default value
    
    subtotal = unit_price + installation_fittings + installation_labor
    tax_rate = 16  # Default VAT rate
    tax_amount = subtotal * (tax_rate / 100)
    total = subtotal + tax_amount
    
    # For multiple units if needed
    quantity = 1  # Default to 1, can be changed based on request
    grand_total = total * quantity
    
    price_data = {
        "unit_price": unit_price,
        "unit_price_formatted": format_currency(unit_price),
        "installation_fittings": installation_fittings,
        "installation_fittings_formatted": format_currency(installation_fittings),
        "installation_labor": installation_labor,
        "installation_labor_formatted": format_currency(installation_labor),
        "subtotal": subtotal,
        "subtotal_formatted": format_currency(subtotal),
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "tax_amount_formatted": format_currency(tax_amount),
        "total": total,
        "total_formatted": format_currency(total),
        "grand_total": grand_total,
        "grand_total_formatted": format_currency(grand_total),
        "quantity": quantity
    }
    
    # Generate structured quotation
    quotation_text = generate_structured_quotation(customer_data, product_data, price_data)
    
    quotation_data = {
        "status": "success",
        "message": "Quotation generated successfully",
        "data": {
            "customer": customer_data,
            "product": product_data,
            "price": price_data,
            "quotation_text": quotation_text
        }
    }
    
    return quotation_data

def format_currency(amount):
    return "{:,.2f}".format(amount)

def generate_structured_quotation(customer_data, product_data, price_data):
    from datetime import datetime
    
    today = datetime.now().strftime("%B %d, %Y")
    today_short = datetime.now().strftime("%Y-%m-%d")
    ref_number = f"QT-{datetime.now().strftime('%Y%m%d')}-{product_data.get('No', '')}"
    
    # Get customer details or use placeholders
    customer_name = customer_data.get('Name', 'Valued Customer') if customer_data else 'Valued Customer'
    customer_address = "P.O. Box 39542 – 00623."
    customer_city = "Nairobi"  # Default city
    customer_phone = customer_data.get('Phone_No', '') if customer_data else ''
    customer_email = customer_data.get('E_Mail', '') if customer_data else ''
    
    # Format the address properly
    address_line = customer_address
    if customer_city:
        if address_line:
            address_line += f", {customer_city}"
        else:
            address_line = customer_city
            
    # Product details
    product_model = product_data.get('Product_Model', '')
    product_description = product_data.get('Description', '')
    
    # Create structured JSON object
    structured_quotation = {
        "metadata": {
            "reference_number": ref_number,
            "date": today,
            "date_iso": today_short,
            # "expiry_date": (datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        },
        "customer": {
            "name": customer_name,
            "address": customer_address,
            "city": customer_city,
            "full_address": address_line,
            "phone": customer_phone,
            "email": customer_email
        },
        "subject": f"SUPPLY OF {product_model} SYSTEM - {product_data.get('No', '')}",
        "requirement": {
            "title": f"{product_model} System",
            "description": f"To supply & installation of {price_data['quantity']} {product_description}."
        },
        "equipment": {
            "description": f"To supply & installation of {price_data['quantity']} {product_description}.",
            "technical_details": f"The {product_model} systems are designed for all domestic heating applications that utilize the high efficiency benefits of solar hot water technology. The integrated systems combine a water storage tank with an efficient solar collector that generates heat from sunlight, providing a cost-effective and environmentally friendly solution."
        },
        "price_schedule": {
            "items": [
                {
                    "id": 1,
                    "description": product_description,
                    "quantity": price_data['quantity'],
                    "rate": price_data['unit_price'],
                    "rate_formatted": price_data['unit_price_formatted'],
                    "amount": price_data['unit_price'],
                    "amount_formatted": price_data['unit_price_formatted']
                },
                {
                    "id": 2,
                    "description": "Installation Fittings & Sundries",
                    "quantity": 1,
                    "rate": price_data['installation_fittings'],
                    "rate_formatted": price_data['installation_fittings_formatted'],
                    "amount": price_data['installation_fittings'],
                    "amount_formatted": price_data['installation_fittings_formatted']
                },
                {
                    "id": 3,
                    "description": "Installation Labour",
                    "quantity": 1,
                    "rate": price_data['installation_labor'],
                    "rate_formatted": price_data['installation_labor_formatted'],
                    "amount": price_data['installation_labor'],
                    "amount_formatted": price_data['installation_labor_formatted']
                }
            ],
            "subtotal": price_data['subtotal'],
            "subtotal_formatted": price_data['subtotal_formatted'],
            "tax": {
                "rate": price_data['tax_rate'],
                "amount": price_data['tax_amount'],
                "amount_formatted": price_data['tax_amount_formatted']
            },
            "total": price_data['total'],
            "total_formatted": price_data['total_formatted'],
            "grand_total": {
                "quantity": price_data['quantity'],
                "amount": price_data['grand_total'],
                "amount_formatted": price_data['grand_total_formatted']
            }
        }
        
    }
    
    return structured_quotation

def fetch_customer_by_field(field: str, value: str):
    import urllib.parse
    encoded_value = urllib.parse.quote(value)

    allowed_fields = ["Phone_No", "Name", "No"]
    if field not in allowed_fields:
        raise ValueError("Invalid search field")

    url = f"{ERP_BASE_URL}/Customer_Card?$filter={field} eq '{encoded_value}'"

    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        data = response.json()
        if not data.get('value'):
            return {"message": "No customer found", "data": None}
        return data
    else:
        raise Exception(f"Failed: {response.status_code} - {response.text}")
