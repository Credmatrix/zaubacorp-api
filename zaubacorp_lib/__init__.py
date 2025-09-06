# ============================================================================
# zaubacorp_lib/__init__.py
# ============================================================================

"""
ZaubaCorp Library - Internal company data extraction library
"""

from .client import ZaubaCorpClient
from .models import SearchFilter, CompanySearchResult, CompanyData
from .exceptions import ZaubaCorpError, SearchError, ExtractionError, NetworkError

__version__ = "1.0.0"
__author__ = "Your Team"
__all__ = [
    "ZaubaCorpClient",
    "SearchFilter",
    "CompanySearchResult",
    "CompanyData",
    "ZaubaCorpError",
    "SearchError",
    "ExtractionError",
    "NetworkError",
    "search_companies",
    "get_company_data",
    "search_and_get_data"
]
