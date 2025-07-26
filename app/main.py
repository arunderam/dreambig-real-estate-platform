from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.v1.routers import api_router
from app.core.firebase import initialize_firebase # type: ignore
from app.db.session import engine
from app.db import models
from app.config import settings

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize Firebase
initialize_firebase()

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

app = FastAPI(
    title="DreamBig Real Estate Platform",
    description="Complete property listing and investment platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/about")
def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/kyc-verification")
def kyc_verification_page(request: Request):
    return templates.TemplateResponse("kyc-verification.html", {"request": request})

@app.get("/profile")
def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/properties")
def properties_page(request: Request):
    return templates.TemplateResponse("properties.html", {"request": request})

@app.get("/properties/{property_id}")
def property_details_page(request: Request, property_id: int):
    return templates.TemplateResponse("property-details.html", {"request": request, "property_id": property_id})

@app.get("/add-property")
def add_property_page(request: Request):
    return templates.TemplateResponse("add-property.html", {"request": request})

@app.get("/investments")
def investments_page(request: Request):
    return templates.TemplateResponse("investments.html", {"request": request})

@app.get("/services")
def services_page(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})

@app.get("/offline")
def offline_page(request: Request):
    return templates.TemplateResponse("offline.html", {"request": request})

@app.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/favicon.ico")
def favicon():
    # Return a simple response instead of a file that doesn't exist
    from fastapi.responses import Response
    return Response(status_code=204)