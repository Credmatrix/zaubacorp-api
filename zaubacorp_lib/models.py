# ============================================================================
# zaubacorp_lib/models.py
# ============================================================================

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import time


class SearchFilter(Enum):
    """Search filter options for typeahead API"""
    COMPANY = "company"
    DIRECTOR = "director"
    TRADEMARK = "trademark"
    ADDRESS = "company_by_address"


@dataclass
class CompanySearchResult:
    """Data class for company search results"""
    id: str
    name: str

    @classmethod
    def from_html_div(cls, div_element):
        """Create CompanySearchResult from HTML div element"""
        company_id = div_element.get('id', '')
        company_name = div_element.get_text(strip=True)
        return cls(id=company_id, name=company_name)


@dataclass
class CompanyData:
    """Data class for complete company data"""
    company_id: str
    rc_sections: Dict
    extraction_timestamp: str
    success: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.extraction_timestamp:
            self.extraction_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
