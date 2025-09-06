# ============================================================================
# zaubacorp_lib/exceptions.py
# ============================================================================

class ZaubaCorpError(Exception):
    """Custom exception for ZaubaCorp operations"""
    pass


class SearchError(ZaubaCorpError):
    """Exception for search operations"""
    pass


class ExtractionError(ZaubaCorpError):
    """Exception for data extraction operations"""
    pass


class NetworkError(ZaubaCorpError):
    """Exception for network-related errors"""
    pass
