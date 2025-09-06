"""
Complete Credmatrix Backend - FastAPI Application
Integrates financial document analysis, company search, and credit report generation
"""

import os
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from concurrent.futures import ThreadPoolExecutor
import httpx
from models import CompanySearchResponse, CompanyDataResponse
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


try:
    from zaubacorp_lib import (
        ZaubaCorpClient,
        SearchFilter,
        CompanySearchResult,
        CompanyData,
        ZaubaCorpError
    )
    ZAUBACORP_AVAILABLE = True
    logger.info("✅ ZaubaCorp library imported successfully")
except ImportError as e:
    logger.warning(f"⚠️  Warning: Could not import zaubacorp_lib: {e}")
    ZAUBACORP_AVAILABLE = False

# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

app = FastAPI(
    title="ZaubaCorp Complete Backend API",
    description="Complete backend for ZaubaCorp - Company search",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

zauba_client = None
thread_pool = ThreadPoolExecutor(max_workers=10)

# Initialize ZaubaCorp client
if ZAUBACORP_AVAILABLE:
    try:
        zauba_client = ZaubaCorpClient(delay_between_requests=1.0)
        logger.info("✅ ZaubaCorp client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Could not initialize ZaubaCorp client: {e}")

# =============================================================================
# API ENDPOINTS - HEALTH & INFO
# =============================================================================


async def run_in_thread(func, *args, **kwargs):
    """Run synchronous function in thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, func, *args, **kwargs)


@app.get("/")
async def root():
    return {
        "message": "ZaubaCorp Complete Backend API",
        "version": "2.0.0",
        "status": "running",
        "services": {
            "zaubacorp": ZAUBACORP_AVAILABLE,
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    # Check ZaubaCorp
    health_status["services"]["zaubacorp"] = "available" if zauba_client else "not_available"

    return health_status

# =============================================================================
# API ENDPOINTS - COMPANY SEARCH (ZaubaCorp)
# =============================================================================


@app.get("/search", response_model=CompanySearchResponse)
async def search_companies(
    query: str,
    filter_type: str = "company",
    max_results: Optional[int] = 10
):
    """Search for companies using ZaubaCorp API"""
    if not zauba_client:
        raise HTTPException(
            status_code=503,
            detail="ZaubaCorp service not available"
        )

    try:
        # Validate filter type
        try:
            search_filter = SearchFilter(filter_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter_type. Must be one of: {[f.value for f in SearchFilter]}"
            )

        # Perform search in thread pool
        results = await run_in_thread(
            zauba_client.search_companies,
            query,
            search_filter,
            max_results
        )

        # Convert results to dict format
        results_dict = [
            {"id": result.id, "name": result.name}
            for result in results
        ]

        return CompanySearchResponse(
            success=True,
            results=results_dict,
            total_found=len(results_dict)
        )

    except ZaubaCorpError as e:
        logger.error(f"ZaubaCorp search error: {str(e)}")
        return CompanySearchResponse(
            success=False,
            results=[],
            total_found=0,
            error_message=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during search"
        )


@app.get("/company/{company_id}", response_model=CompanyDataResponse)
async def get_company_data(company_id: str):
    """Get complete company data by company ID from ZaubaCorp"""
    if not zauba_client:
        raise HTTPException(
            status_code=503,
            detail="ZaubaCorp service not available"
        )

    try:
        # Get company data in thread pool
        company_data = await run_in_thread(
            zauba_client.get_company_data,
            company_id
        )

        return CompanyDataResponse(
            success=company_data.success,
            company_id=company_data.company_id,
            rc_sections=company_data.rc_sections,
            extraction_timestamp=company_data.extraction_timestamp,
            error_message=company_data.error_message
        )

    except Exception as e:
        logger.error(f"Unexpected error getting company data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during data extraction"
        )

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
