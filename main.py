from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from triaging.routes import router as triaging_router
from product_manual.routes import router as product_manual_router
from erp.routes import router as erp_router

app = FastAPI(
     title="Solar Hot Water System API",
    description="This API assists in configuring the optimal solar hot water system by guiding users through the triaging and sizing processes. The API dynamically recommends system configurations based on user input, helping to generate tailored proposals and quotations.",
    
)

# Add cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-solar-hot-water-frontend-xakt.vercel.app/", "http://localhost:5173/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(triaging_router)
app.include_router(product_manual_router)
app.include_router(erp_router)


@app.get('/')
def health_check():
    return JSONResponse(content={"status": "Wellcome. The server is up and Running!"})

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

