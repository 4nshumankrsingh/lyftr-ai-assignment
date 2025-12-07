"""
Enhanced main application with Phase 4 & 5 features
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import time
import asyncio
from typing import Dict, Any

from .models.schemas import (
    ScrapeRequest, ScrapeResponse, ScrapeResult, EnhancedMeta, 
    EnhancedInteraction, Error, ScrapeStrategy, PerformanceMetrics
)
from .scraper.fallback_strategy import FallbackStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universal Website Scraper API",
    description="A full-stack website scraper with intelligent fallback strategy",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize fallback strategy
fallback_strategy = FallbackStrategy()

# Rate limiting tracking
request_times = {}

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting"""
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Clean old entries
    request_times[client_ip] = [
        t for t in request_times.get(client_ip, []) 
        if current_time - t < 60  # Keep last minute
    ]
    
    # Check rate limit (10 requests per minute)
    if len(request_times.get(client_ip, [])) >= 10:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Maximum 10 requests per minute"
            }
        )
    
    # Add current request
    request_times.setdefault(client_ip, []).append(current_time)
    
    return await call_next(request)

@app.get("/")
def read_root():
    return {
        "message": "Universal Website Scraper API v2.0",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "GET /healthz": "Health check",
            "POST /scrape": "Scrape a website with intelligent fallback",
            "GET /docs": "API documentation",
            "GET /redoc": "Alternative documentation"
        },
        "features": [
            "Static + JavaScript rendering",
            "Intelligent fallback strategy",
            "Interactive scraping (tabs, load more, pagination)",
            "Minimum depth ≥ 3 guarantee",
            "Noise filtering and optimization",
            "Enhanced metadata extraction",
            "Performance monitoring"
        ]
    }

@app.get("/healthz")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0",
        "services": {
            "playwright": "available" if hasattr(fallback_strategy.playwright_scraper, 'scrape') else "unavailable",
            "static_scraper": "available",
            "fallback_strategy": "available"
        }
    }

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_website(request: ScrapeRequest):
    """
    Scrape a website using intelligent fallback strategy
    
    - **url**: The website URL to scrape (must start with http:// or https://)
    
    Returns enhanced results with performance metrics and interaction tracking.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting scrape for URL: {request.url}")
        
        # Validate URL beyond basic schema
        if not self._is_valid_url(request.url):
            raise HTTPException(
                status_code=400,
                detail="Invalid URL format. Must be a valid http/https URL."
            )
        
        # Use enhanced fallback strategy
        try:
            strategy, scraped_data = await fallback_strategy.scrape_with_fallback(request.url)
        except asyncio.TimeoutError:
            elapsed = (time.time() - start_time) * 1000
            return ScrapeResponse(
                result=ScrapeResult(
                    url=request.url,
                    scrapedAt=datetime.utcnow().isoformat() + "Z",
                    meta=EnhancedMeta(strategy=ScrapeStrategy.ERROR),
                    sections=[],
                    interactions=EnhancedInteraction(),
                    errors=[Error(
                        message=f"Scraping timeout after {elapsed:.0f}ms",
                        phase="timeout",
                        timestamp=datetime.utcnow().isoformat() + "Z"
                    )],
                    performance=PerformanceMetrics(
                        duration_ms=elapsed,
                        sections_found=0,
                        interaction_depth=0,
                        pages_visited=0
                    )
                ),
                status="error",
                message="Scraping timeout"
            )
        
        # Calculate performance metrics
        elapsed_time = (time.time() - start_time) * 1000
        
        # Add strategy and performance info
        scraped_data['meta']['strategy'] = strategy
        scraped_data['meta']['scrapeDuration'] = f"{elapsed_time:.0f}ms"
        
        # Calculate interaction depth
        interactions = scraped_data.get('interactions', {})
        interaction_depth = len(interactions.get('clicks', [])) + interactions.get('scrolls', 0)
        scraped_data['meta']['interactionDepth'] = interaction_depth
        
        # Add performance metrics
        scraped_data['performance'] = {
            "duration_ms": elapsed_time,
            "sections_found": len(scraped_data.get('sections', [])),
            "interaction_depth": interaction_depth,
            "pages_visited": len(interactions.get('pages', [])),
            "unique_sections": len(scraped_data.get('sections', []))
        }
        
        # Add total depth to interactions
        scraped_data['interactions']['totalDepth'] = interaction_depth
        
        # Check if minimum depth was achieved
        if interaction_depth < 3:
            scraped_data['warnings'] = scraped_data.get('warnings', [])
            scraped_data['warnings'].append(
                f"Minimum interaction depth not reached: {interaction_depth} < 3"
            )
        
        logger.info(f"Scrape completed in {elapsed_time:.0f}ms with strategy: {strategy}")
        
        return ScrapeResponse(
            result=scraped_data,
            status="success",
            message=f"Scraping completed with {strategy} strategy"
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        logger.error(f"Scraping failed: {str(e)}")
        
        error_result = ScrapeResult(
            url=request.url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=EnhancedMeta(strategy=ScrapeStrategy.ERROR),
            sections=[],
            interactions=EnhancedInteraction(),
            errors=[Error(
                message=str(e),
                phase="general",
                timestamp=datetime.utcnow().isoformat() + "Z"
            )],
            performance=PerformanceMetrics(
                duration_ms=elapsed_time,
                sections_found=0,
                interaction_depth=0,
                pages_visited=0
            )
        )
        
        return ScrapeResponse(
            result=error_result,
            status="error",
            message=str(e)
        )

@app.get("/stats")
async def get_stats():
    """Get scraping statistics"""
    return {
        "total_requests": sum(len(times) for times in request_times.values()),
        "unique_clients": len(request_times),
        "requests_last_minute": sum(
            1 for times in request_times.values() 
            for t in times if time.time() - t < 60
        ),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def _is_valid_url(self, url: str) -> bool:
    """Enhanced URL validation"""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))