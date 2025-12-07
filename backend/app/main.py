from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from .models.schemas import ScrapeRequest, ScrapeResponse, ScrapeResult, Meta, Interaction, Error
from .scraper.static_scraper import StaticScraper

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
    Scrape a website and return structured JSON
    
    - **url**: The website URL to scrape (must start with http:// or https://)
    """
    try:
        logger.info(f"Scraping URL: {request.url}")
        
        # Create scraper instance
        scraper = StaticScraper(request.url)
        
        # Perform scraping
        scraped_data = await scraper.scrape()
        
        # Build response
        result = ScrapeResult(
            url=scraped_data["url"],
            scrapedAt=datetime.utcnow(),
            meta=Meta(**scraped_data["meta"]),
            sections=scraped_data["sections"],
            interactions=Interaction(clicks=[], scrolls=0, pages=[request.url]),
            errors=[Error(**error) for error in scraped_data.get("errors", [])]
        )
        
        return ScrapeResponse(result=result)
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        # Return error response
        result = ScrapeResult(
            url=request.url,
            scrapedAt=datetime.utcnow(),
            meta=Meta(),
            sections=[],
            interactions=Interaction(),
            errors=[Error(message=str(e), phase="general")]
        )
        return ScrapeResponse(result=result)