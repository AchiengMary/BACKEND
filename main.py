from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from triaging.routes import router as triaging_router
from product_manual.routes import router as product_manual_router
from erp.routes import router as erp_router
from Auth.routes import router as auth_router
from sunshine.routes import router as sunshine_router
from customer_proposal.database import init_db
from customer_proposal.routes import api_router

app = FastAPI(
     title="Solar Hot Water System API",
    description="This API assists in configuring the optimal solar hot water system by guiding users through the triaging and sizing processes. The API dynamically recommends system configurations based on user input, helping to generate tailored proposals and quotations.",
    
)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()


# Add cors middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173/", "https://f1-f.vercel.app/"],
    allow_origins=["http://localhost:5173", "https://f1-f.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(triaging_router)
app.include_router(product_manual_router)
app.include_router(erp_router)
app.include_router(auth_router)
app.include_router(sunshine_router)

@app.get('/')
def health_check():
    return JSONResponse(content={"status": "Wellcome. The server is up and Running!"})
