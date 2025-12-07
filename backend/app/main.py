from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from .models.schemas import ScrapeRequest, ScrapeResponse, ScrapeResult, Meta, Interaction, Error, Section, Content, Link, Image, SectionType
from .scraper.fallback_strategy import FallbackStrategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universal Website Scraper",
    description="A full-stack website scraper with JSON viewer for Lyftr AI assignment",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize fallback strategy
fallback_strategy = FallbackStrategy()

@app.get("/")
def read_root():
    return {
        "message": "Universal Website Scraper API",
        "endpoints": {
            "GET /healthz": "Health check",
            "POST /scrape": "Scrape a website"
        }
    }

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_website(request: ScrapeRequest):
    """
    Scrape a website using intelligent fallback strategy
    
    - **url**: The website URL to scrape (must start with http:// or https://)
    """
    try:
        logger.info(f"Scraping URL: {request.url}")
        
        # Use fallback strategy
        strategy, scraped_data = await fallback_strategy.scrape_with_fallback(request.url)
        
        # Add strategy info to result
        scraped_data['meta']['strategy'] = strategy
        
        return ScrapeResponse(result=scraped_data)
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        
        # Create error response
        result = ScrapeResult(
            url=request.url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=Meta(strategy="error"),
            sections=[],
            interactions=Interaction(),
            errors=[Error(message=str(e), phase="general")]
        )
        return ScrapeResponse(result=result)