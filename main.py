from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from triaging.routes import router as triaging_router

app = FastAPI(
     title="Solar Hot Water System API",
    description="This API assists in configuring the optimal solar hot water system by guiding users through the triaging and sizing processes. The API dynamically recommends system configurations based on user input, helping to generate tailored proposals and quotations.",
    
)

# Add cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(triaging_router)


@app.get('/')
def health_check():
    return JSONResponse(content={"status": "Wellcome. The server is up and Running!"})