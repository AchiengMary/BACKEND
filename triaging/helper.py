

def generate_prompt_from_questionnaire(data: QuestionnaireResponse) -> str:
    """Convert questionnaire data to a structured prompt for embedding"""
    return f"""
    Property Type: {data.propertyType}
    Number of Occupants: {data.occupants}
    Current Heating System: {data.currentHeating}
    Water Usage Pattern: {data.waterUsage}
    Available Roof Space: {data.roofSpace}
    Budget Range: {data.budget}
    Location Type: {data.location}
    Daily Sunlight Hours: {data.sunlightHours}
    Existing Solar System: {data.existingSystem}
    Installation Timeline: {data.timeline}
    """

def get_recommendations_from_pinecone(vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
    """Query Pinecone for the most similar systems based on the embedding vector"""
    try:
        query_response = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )
        return query_response.matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Pinecone: {str(e)}")

def analyze_requirements(data: QuestionnaireResponse) -> Dict[str, Any]:
    """Analyze the requirements based on questionnaire data"""
    # Extract numerical values from string ranges
    occupants_map = {
        "1-2": 2, "3-4": 4, "5-6": 6, "7-10": 10, "10+": 15
    }
    
    roof_space_map = {
        "<5": 4, "5-10": 7.5, "10-20": 15, "20-50": 35, "50+": 60
    }
    
    sunlight_map = {
        "<3 hours": 2, "3-5 hours": 4, "5-7 hours": 6, "7+ hours": 8
    }
    
    # Water consumption estimation (liters per person per day)
    water_usage_per_person = {
        "Light (mostly showers)": 30,
        "Moderate (showers + appliances)": 50,
        "Heavy (multiple baths daily)": 80,
        "Commercial use": 100
    }
    
    # Estimate daily hot water requirement
    num_occupants = occupants_map.get(data.occupants, 4)
    daily_usage = water_usage_per_person.get(data.waterUsage, 50)
    total_daily_hot_water = num_occupants * daily_usage
    
    # Estimate system size based on available roof space and daily requirement
    available_roof = roof_space_map.get(data.roofSpace, 15)
    sunlight_hours = sunlight_map.get(data.sunlightHours, 5)
    
    # Return analysis results
    return {
        "estimated_occupants": num_occupants,
        "daily_hot_water_needed": total_daily_hot_water,
        "available_roof_space": available_roof,
        "effective_sunlight_hours": sunlight_hours,
        "system_size_recommendation": {
            "min_capacity_liters": max(100, total_daily_hot_water * 0.8),
            "ideal_capacity_liters": total_daily_hot_water * 1.2,
            "collector_area_needed": total_daily_hot_water / (40 * sunlight_hours)  # Rough estimate
        }
    }