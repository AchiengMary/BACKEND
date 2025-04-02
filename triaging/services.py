from fastapi import HTTPException

# Helper function to process model response
def process_model_response(response):
    """Extracts the list of questions from the model's response."""
    try:
        
        # Extract the questions from the content, assuming they are separated by '\n'
        question_list = response.content.strip().split("\n")

        # Ensure we got exactly 5 questions
        if len(question_list) != 5:
            raise ValueError("The model did not return the expected number of questions.")
        
        return question_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing the model's response: {str(e)}")