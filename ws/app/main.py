from fastapi import FastAPI
from app.api.routes.antrian import antrian
from app.api.routes.antrianbpjs import ws_bpjs
from app.api.routes.adminantrian import adminantrian
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # HTTPSRedirectMiddleware
)
# app.add_middleware(HTTPSRedirectMiddleware)
# app = FastAPI(docs_url=None,redoc_url=None)
app.include_router(antrian,prefix='/api/v1/prod',tags=['Mobile JKN API'])
app.include_router(ws_bpjs,prefix='/wsbpjs',tags=['WS BPJS'])
app.include_router(adminantrian,prefix='/adminantrian',tags=['Proses Antrian'])


