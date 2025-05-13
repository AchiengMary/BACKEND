from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/solar",
    tags=["Solar Radiation"]
)

OPENCAGE_KEY = os.getenv("OPENCAGE_KEY")

class SolarResponse(BaseModel):
    city: str
    latitude: float
    longitude: float
    monthly_radiation: dict
    annual_average: float

@router.get("/radiation", response_model=SolarResponse)
async def get_solar_radiation(city: str = Query(..., example="Nairobi")):
    if not OPENCAGE_KEY:
        raise HTTPException(status_code=500, detail="OpenCage API key not set in environment.")

    # Step 1: Get coordinates from OpenCage API
    geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={city}&key={OPENCAGE_KEY}"
    async with httpx.AsyncClient() as client:
        geo_response = await client.get(geocode_url)

    if geo_response.status_code != 200 or not geo_response.json()["results"]:
        raise HTTPException(status_code=404, detail="City not found in OpenCage data.")

    location = geo_response.json()["results"][0]["geometry"]
    lat, lon = location["lat"], location["lng"]

    # Step 2: Fetch monthly solar radiation from NASA POWER (climatology endpoint)
    nasa_url = (
        f"https://power.larc.nasa.gov/api/temporal/climatology/point?"
        f"parameters=ALLSKY_SFC_SW_DWN&latitude={lat}&longitude={lon}"
        f"&community=RE&format=JSON"
    )

    async with httpx.AsyncClient() as client:
        nasa_response = await client.get(nasa_url)

    if nasa_response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to retrieve NASA solar data.")

    parameters = nasa_response.json().get("properties", {}).get("parameter", {})
    monthly_data = parameters.get("ALLSKY_SFC_SW_DWN")

    if not monthly_data:
        raise HTTPException(status_code=500, detail="Missing solar radiation data from NASA.")

    # Compute annual average
    monthly_values = list(monthly_data.values())
    annual_average = round(sum(monthly_values) / len(monthly_values), 2)

    return SolarResponse(
        city=city,
        latitude=lat,
        longitude=lon,
        monthly_radiation=monthly_data,
        annual_average=annual_average
    )
