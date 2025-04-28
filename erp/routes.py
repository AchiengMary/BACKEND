from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
# from .erp_client import fetch_entity, fetch_product_by_number, fetch_customer_by_phone_number, get_product_quotation
from fastapi import APIRouter, HTTPException, Query
from .erp_client import fetch_entity, fetch_product_by_number, fetch_customer_by_phone_number, fetch_customer_by_field, get_product_quotation

router = APIRouter(prefix="/erp", tags=["ERP"])

class QuotationRequest(BaseModel):
    product_number: str
    phone_number: Optional[str] = None
    name: Optional[str] = None


@router.get("/{entity_name}")
def get_entity_list(entity_name: str):
    try:
        return fetch_entity(entity_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{entity_name}/{entity_id}")
def get_entity_item(entity_name: str, entity_id: str):
    try:
        return fetch_entity(entity_name, entity_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@router.get("/Customer_Card/Phone_No/{Phone_No}")
def get_customer_by_phone_number(Phone_No: str):
    try:
        return fetch_customer_by_phone_number(Phone_No)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/products/number/{product_number}")
def get_product_by_number(product_number: str):
    try:
        return fetch_product_by_number(product_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/quotation")
def create_product_quotation(request: QuotationRequest):
    try:
        return get_product_quotation(request.product_number, request.phone_number, request.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/Customer_Card/{field}/{value}")
def get_customer_by_various_fields(field: str, value: str):
    try:
        return fetch_customer_by_field(field, value)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
