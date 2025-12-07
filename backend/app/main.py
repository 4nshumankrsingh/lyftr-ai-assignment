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
    ScrapeRequest, ScrapeResponse, ScrapeResult, Meta,
    Interaction, Error, ScrapeStrategy, PerformanceMetrics
)

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

# Initialize fallback strategy lazily
_fallback_strategy = None

def get_fallback_strategy():
    """Lazy initialization of FallbackStrategy"""
    global _fallback_strategy
    if _fallback_strategy is None:
        from .scraper.fallback_strategy import FallbackStrategy
        _fallback_strategy = FallbackStrategy()
    return _fallback_strategy

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
    strategy = get_fallback_strategy()

    # Better Playwright availability check
    playwright_available = "unavailable"
    try:
        # If the strategy already has an initialized scraper, inspect it
        if getattr(strategy, 'playwright_scraper', None) is not None:
            if hasattr(strategy.playwright_scraper, 'scrape'):
                playwright_available = "available"
            else:
                playwright_available = "initialized (no scrape method)"
        else:
            # Try to lazy-initialize a tester instance without launching a browser
            try:
                from .scraper.playwright_scraper import PlaywrightScraper
                test_scraper = PlaywrightScraper(headless=True)
                if hasattr(test_scraper, 'scrape'):
                    playwright_available = "test-success"
            except Exception as e:
                # Importing or constructing may fail if Playwright isn't installed
                playwright_available = f"error: {str(e)[:50]}"
    except Exception as e:
        playwright_available = f"error: {str(e)[:50]}"

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0",
        "services": {
            "static_scraper": "available",
            "fallback_strategy": "available",
            "playwright": playwright_available
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

        # Validate URL
        if not _is_valid_url(request.url):
            raise HTTPException(
                status_code=400,
                detail="Invalid URL format. Must be a valid http/https URL."
            )

        # Use fallback strategy with timeout
        strategy = get_fallback_strategy()

        # Set a timeout for the entire scraping operation
        try:
            strategy_used, scraped_data = await asyncio.wait_for(
                strategy.scrape_with_fallback(request.url),
                timeout=30.0  # 30 second timeout for entire operation
            )
        except asyncio.TimeoutError:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"Scraping timeout after {elapsed:.0f}ms")

            # Try to get static results as fallback (best-effort)
            try:
                from .scraper.static_scraper import StaticScraper
                static_scraper = StaticScraper()
                static_result = await static_scraper.scrape(request.url)
                scraped_data = static_result.dict()
                strategy_used = "static_timeout_fallback"
                logger.info("Used static scraper as timeout fallback")
            except Exception as static_error:
                logger.error(f"Static fallback after timeout also failed: {static_error}")
                return ScrapeResponse(
                    result=ScrapeResult(
                        url=request.url,
                        scrapedAt=datetime.utcnow().isoformat() + "Z",
                        meta=Meta(),
                        sections=[],
                        interactions=Interaction(),
                        errors=[Error(
                            message=f"Scraping timeout after {elapsed:.0f}ms and static fallback also failed",
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

        # Add strategy info safely
        try:
            scraped_data.setdefault('meta', {})
            scraped_data['meta']['strategy'] = strategy_used
        except Exception:
            logger.debug("Could not set meta.strategy on scraped_data; initializing meta object")
            scraped_data['meta'] = {'strategy': strategy_used}

        # Calculate interaction depth (defensive)
        interactions = scraped_data.get('interactions', {}) if isinstance(scraped_data, dict) else {}
        interaction_depth = 0
        try:
            interaction_depth = len(interactions.get('clicks', [])) + interactions.get('scrolls', 0)
        except Exception:
            interaction_depth = 0

        # Add performance metrics if not present
        if 'performance' not in scraped_data:
            scraped_data['performance'] = {
                "duration_ms": elapsed_time,
                "sections_found": len(scraped_data.get('sections', [])),
                "interaction_depth": interaction_depth,
                "pages_visited": len(interactions.get('pages', [])) if isinstance(interactions, dict) else 0,
                "unique_sections": len(scraped_data.get('sections', []))
            }

        # Add total depth to interactions safely
        try:
            scraped_data.setdefault('interactions', {})
            scraped_data['interactions']['totalDepth'] = interaction_depth
        except Exception:
            logger.debug("Failed to write interactions.totalDepth")

        # Check if minimum depth was achieved
        if interaction_depth < 3:
            scraped_data.setdefault('warnings', [])
            scraped_data['warnings'].append(
                f"Minimum interaction depth not reached: {interaction_depth} < 3"
            )

        logger.info(f"Scrape completed in {elapsed_time:.0f}ms with strategy: {strategy_used}")

        return ScrapeResponse(
            result=scraped_data,
            status="success",
            message=f"Scraping completed with {strategy_used} strategy"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        logger.exception(f"Scraping failed: {str(e)}")

        # Try to get at least some static data (best-effort fallback)
        try:
            from .scraper.static_scraper import StaticScraper
            static_scraper = StaticScraper()
            static_result = await static_scraper.scrape(request.url)
            scraped_data = static_result.dict()
            scraped_data.setdefault('meta', {})
            scraped_data['meta']['strategy'] = "static_error_fallback"

            logger.info("Used static scraper as error fallback")

            return ScrapeResponse(
                result=scraped_data,
                status="partial",
                message=f"Scraping completed with static fallback after error: {str(e)}"
            )
        except Exception as static_error:
            logger.exception(f"Static fallback also failed: {static_error}")
            # If everything fails, return structured error
            error_result = ScrapeResult(
                url=request.url,
                scrapedAt=datetime.utcnow().isoformat() + "Z",
                meta=Meta(),
                sections=[],
                interactions=Interaction(),
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

def _is_valid_url(url: str) -> bool:
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