from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
# from .erp_client import fetch_entity, fetch_product_by_number, fetch_customer_by_phone_number, get_product_quotation
from fastapi import APIRouter, HTTPException, Query
from .erp_client import fetch_entity, fetch_product_by_number, fetch_customer_by_phone_number, fetch_customer_by_field, get_product_quotation, post_to_erp, create_sales_quote_line, fetch_referrence_number

router = APIRouter(prefix="/erp", tags=["ERP"])

class QuotationRequest(BaseModel):
    product_number: str
    phone_number: Optional[str] = None
    name: Optional[str] = None

class SalesQuoteRequest(BaseModel):
    """Request model for creating a Sales Quote in the ERP system"""
    Sell_to_Customer_No: str
    Salesperson_code: str
    Responsibility_Center: str
    Assigned_User_ID: str
    
class SalesQuoteLineRequest(BaseModel):
    """Request model for creating a Sales Quote Line item in the ERP system"""
    Document_Type: str
    Document_No: str
    Type: str
    Quantity: int
    No: str
    
@router.post("/sales-quote")
def create_sales_quote(request: SalesQuoteRequest):
   
    try:
        # Based on the Postman screenshot, format data exactly as shown
        formatted_data = {
            "Sell_to_Customer_No": request.Sell_to_Customer_No,
            "Salesperson_Code": request.Salesperson_code,
            "Responsibility_Center": request.Responsibility_Center,
            "Assigned_User_ID": request.Assigned_User_ID
        }
        
        # Post the data to the ERP system
        result = post_to_erp("Sales_Quote", formatted_data)
        
        return {
            "status": "success",
            "message": "Sales quote created successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/sales-quote-line")
def add_sales_quote_line(request: SalesQuoteLineRequest):
    """
    Add a line item to an existing sales quote in the ERP system
    """
    try:
        # Format data based on your screenshot
        formatted_data = {
            "Document_Type": request.Document_Type,
            "Document_No": request.Document_No,
            "Type": request.Type,
            "Quantity": request.Quantity,
            "No": request.No
        }
        
        
        # Create the sales quote line
        result = create_sales_quote_line(formatted_data)
        
        return {
            "status": "success",
            "message": "Sales quote line item added successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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
    
@router.get("/get/sales-quote/{reference:path}")
def get_proposal_by_reference(reference: str):
    try:
        print(f"Fetching sales quote with reference: {reference}")
        return fetch_referrence_number(reference)
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
