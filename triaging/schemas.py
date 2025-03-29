from pydantic import BaseModel

class UserQuery(BaseModel):
    user_query: str  # The user's inquiry/question