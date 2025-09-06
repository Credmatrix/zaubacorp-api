# ============================================================================
# zaubacorp_lib/client.py
# ============================================================================

import requests
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Optional

from .models import SearchFilter, CompanySearchResult, CompanyData
from .exceptions import ZaubaCorpError, SearchError, ExtractionError, NetworkError


class ZaubaCorpClient:
    """ZaubaCorp client for searching companies and extracting data"""

    def __init__(self, delay_between_requests: float = 1.0):
        """Initialize ZaubaCorp client"""
        self.base_url = "https://www.zaubacorp.com"
        self.delay = delay_between_requests
        self.session = requests.Session()

        # Set headers to mimic browser requests
        self.session.headers.update({
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Cookie': 'ZCSESSID=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiIiwiYW5vbnltb3VzX3V1aWQiOiIwOWEyOGIyYS1lYzkwLTQ2MzEtYWIxNS02YmEwMzY1Yzk0ZTAiLCJleHAiOjE3NTc3MjY2MjV9.KvcyWkqm_pSH7R3CqJTj3i3WnN0aH-rqrmrxvbxE6Y0; cf_clearance=D8lc3AW6Taig_HH5mFxyHkf6rFP01y_8tXTzzxs.Rok-1757152122-1.2.1.1-7ZqY1m4FWu8UUm35rIjvvJLgDn1vt_7Syn7RvQRAidy4F.GdXv0vFSLC72u128chTrfjBYfD2cRyFZh1mcs3W28E1yzQcYHdKWXWTJ7CwVCr80SuKlQAsrc7tHcupCJttX3xQYGlW1lzPUs8x4TLynd.zs1BPw8Tclh3rZgzX_huCupRuJRecKkHLEsyDY3b4wR3wGwH2HN1i4cTlCQCMtfFpiWf6xjSCU9V5Kc5KpI'
        })

    def _search_companies_urllib(self, query: str, filter_type: SearchFilter = SearchFilter.COMPANY) -> Optional[str]:
        """Alternative search method using urllib for typeahead API"""
        try:
            url = f"{self.base_url}/typeahead"

            # Prepare form data
            data = {
                'search': query,
                'filter': filter_type.value
            }

            # Encode the data
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')

            # Create request
            req = urllib.request.Request(url, data=encoded_data, method='POST')

            # Add headers to match working curl command
            req.add_header(
                'user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
            req.add_header(
                'Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.9')
            req.add_header('Accept-Encoding', 'gzip, deflate')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            req.add_header('DNT', '1')
            req.add_header('Connection', 'keep-alive')
            req.add_header('Cache-Control', 'max-age=0')
            req.add_header('Cookie', 'ZCSESSID=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiIiwiYW5vbnltb3VzX3V1aWQiOiIwOWEyOGIyYS1lYzkwLTQ2MzEtYWIxNS02YmEwMzY1Yzk0ZTAiLCJleHAiOjE3NTc3MjY2MjV9.KvcyWkqm_pSH7R3CqJTj3i3WnN0aH-rqrmrxvbxE6Y0; cf_clearance=D8lc3AW6Taig_HH5mFxyHkf6rFP01y_8tXTzzxs.Rok-1757152122-1.2.1.1-7ZqY1m4FWu8UUm35rIjvvJLgDn1vt_7Syn7RvQRAidy4F.GdXv0vFSLC72u128chTrfjBYfD2cRyFZh1mcs3W28E1yzQcYHdKWXWTJ7CwVCr80SuKlQAsrc7tHcupCJttX3xQYGlW1lzPUs8x4TLynd.zs1BPw8Tclh3rZgzX_huCupRuJRecKkHLEsyDY3b4wR3wGwH2HN1i4cTlCQCMtfFpiWf6xjSCU9V5Kc5KpI')

            with urllib.request.urlopen(req, timeout=30) as response:
                if response.code == 200:
                    content = response.read()
                    # Handle gzip encoding if present
                    if response.headers.get('Content-Encoding') == 'gzip':
                        import gzip
                        content = gzip.decompress(content)
                    return content.decode('utf-8')
                else:
                    return None
        except Exception as e:
            print(f"urllib search error: {e}")
            return None

    def search_companies(self,
                         query: str,
                         filter_type: SearchFilter = SearchFilter.COMPANY,
                         max_results: Optional[int] = None) -> List[CompanySearchResult]:
        """Search for companies using typeahead API"""
        try:
            time.sleep(self.delay)

            # Try urllib method first (working method)
            response_text = self._search_companies_urllib(query, filter_type)

            if not response_text:
                # Fallback to requests session if urllib fails
                try:
                    url = f"{self.base_url}/typeahead"
                    data = {
                        'search': query,
                        'filter': filter_type.value
                    }

                    response = self.session.post(url, data=data, timeout=30)
                    response.raise_for_status()
                    response_text = response.text

                except requests.exceptions.RequestException as e:
                    raise NetworkError(
                        f"Both urllib and requests search methods failed. Last error: {str(e)}")

            # Parse HTML response
            soup = BeautifulSoup(response_text, 'html.parser')
            divs = soup.find_all('div', class_='show')

            results = []
            for div in divs:
                try:
                    result = CompanySearchResult.from_html_div(div)
                    results.append(result)

                    if max_results and len(results) >= max_results:
                        break

                except Exception:
                    continue

            return results

        except NetworkError:
            raise
        except Exception as e:
            raise SearchError(f"Search parsing failed: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'\[email.*?protected\]', '[email protected]', text)
        return text

    def _extract_table_data(self, table) -> List[Dict]:
        """Extract data from a table element"""
        if not table:
            return []

        data = []
        rows = table.find_all('tr')

        for row in rows:
            row_data = {}
            cells = row.find_all(['td', 'th'])

            if len(cells) == 2:
                key = self._clean_text(cells[0].get_text())
                value = self._clean_text(cells[1].get_text())
                if key and value:
                    row_data = {key: value}
            elif len(cells) > 2:
                row_data = {}
                for i, cell in enumerate(cells):
                    cell_text = self._clean_text(cell.get_text())
                    if cell_text:
                        row_data[f"column_{i}"] = cell_text

            if row_data:
                data.append(row_data)

        return data

    def _extract_rc_sections(self, soup) -> Dict:
        """Extract all sections with class 'rc'"""
        rc_sections = {}
        rc_divs = soup.find_all('div', class_='rc')

        for div in rc_divs:
            title_elem = div.find('h3', class_='rh')
            if title_elem:
                section_title = self._clean_text(title_elem.get_text())
            else:
                section_title = f"section_{len(rc_sections)}"

            section_data = {}

            paragraphs = div.find_all('p', class_='rp')
            if paragraphs:
                descriptions = [self._clean_text(
                    p.get_text()) for p in paragraphs]
                section_data['descriptions'] = [
                    desc for desc in descriptions if desc]

            tables = div.find_all('table')
            if tables:
                section_data['tables'] = []
                for i, table in enumerate(tables):
                    table_data = self._extract_table_data(table)
                    if table_data:
                        caption = table.find('caption')
                        caption_text = self._clean_text(
                            caption.get_text()) if caption else f"table_{i}"
                        section_data['tables'].append({
                            'caption': caption_text,
                            'data': table_data
                        })

            if section_data:
                rc_sections[section_title] = section_data

        return rc_sections

    def _fetch_html_urllib(self, company_id: str) -> Optional[str]:
        """Alternative method using urllib for fetching HTML"""
        try:
            url = f"{self.base_url}/{company_id}"

            req = urllib.request.Request(url)
            req.add_header(
                'User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
            req.add_header(
                'Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.9')
            req.add_header('Accept-Encoding', 'gzip, deflate')
            req.add_header('DNT', '1')
            req.add_header('Connection', 'keep-alive')
            req.add_header('Upgrade-Insecure-Requests', '1')
            req.add_header('Cookie', 'ZCSESSID=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiIiwiYW5vbnltb3VzX3V1aWQiOiIwOWEyOGIyYS1lYzkwLTQ2MzEtYWIxNS02YmEwMzY1Yzk0ZTAiLCJleHAiOjE3NTc3MjY2MjV9.KvcyWkqm_pSH7R3CqJTj3i3WnN0aH-rqrmrxvbxE6Y0; cf_clearance=D8lc3AW6Taig_HH5mFxyHkf6rFP01y_8tXTzzxs.Rok-1757152122-1.2.1.1-7ZqY1m4FWu8UUm35rIjvvJLgDn1vt_7Syn7RvQRAidy4F.GdXv0vFSLC72u128chTrfjBYfD2cRyFZh1mcs3W28E1yzQcYHdKWXWTJ7CwVCr80SuKlQAsrc7tHcupCJttX3xQYGlW1lzPUs8x4TLynd.zs1BPw8Tclh3rZgzX_huCupRuJRecKkHLEsyDY3b4wR3wGwH2HN1i4cTlCQCMtfFpiWf6xjSCU9V5Kc5KpI')

            with urllib.request.urlopen(req, timeout=30) as response:
                if response.code == 200:
                    content = response.read()
                    if response.headers.get('Content-Encoding') == 'gzip':
                        import gzip
                        content = gzip.decompress(content)
                    return content.decode('utf-8')
                else:
                    return None
        except Exception:
            return None

    def _fetch_html(self, company_id: str) -> Optional[str]:
        """Fetch HTML content for a company"""
        try:
            return self._fetch_html_urllib(company_id)
        except requests.exceptions.RequestException:
            return self._fetch_html_urllib(company_id)

    def get_company_data(self, company_id: str) -> CompanyData:
        """Get complete company data by company ID"""
        try:
            html_content = self._fetch_html(company_id)
            if not html_content:
                return CompanyData(
                    company_id=company_id,
                    rc_sections={},
                    extraction_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    success=False,
                    error_message="Failed to fetch HTML content"
                )

            soup = BeautifulSoup(html_content, 'html.parser')
            rc_sections = self._extract_rc_sections(soup)

            return CompanyData(
                company_id=company_id,
                rc_sections=rc_sections,
                extraction_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                success=True
            )

        except Exception as e:
            return CompanyData(
                company_id=company_id,
                rc_sections={},
                extraction_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                success=False,
                error_message=str(e)
            )

    def search_and_get_data(self,
                            query: str,
                            exact_match: bool = False,
                            max_search_results: int = 5) -> List[CompanyData]:
        """Search for companies and get their data in one call"""
        try:
            search_results = self.search_companies(
                query, max_results=max_search_results)

            if exact_match:
                search_results = [
                    result for result in search_results
                    if query.lower() in result.name.lower()
                ]

            company_data_list = []
            for result in search_results:
                company_data = self.get_company_data(result.id)
                company_data_list.append(company_data)

            return company_data_list

        except Exception as e:
            raise ZaubaCorpError(
                f"Search and data extraction failed: {str(e)}")
