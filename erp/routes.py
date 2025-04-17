from fastapi import APIRouter, HTTPException
from .erp_client import fetch_entity, fetch_product_by_number

router = APIRouter(prefix="/erp", tags=["ERP"])

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
    
@router.get("/products/number/{product_number}")
def get_product_by_number(product_number: str):
    try:
        return fetch_product_by_number(product_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))