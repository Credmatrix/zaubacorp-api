# ============================================================================
# zaubacorp_lib/client.py
# ============================================================================

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Optional
import atexit

from .models import SearchFilter, CompanySearchResult, CompanyData
from .exceptions import ZaubaCorpError, SearchError, ExtractionError, NetworkError


class ZaubaCorpClient:
    """ZaubaCorp client for searching companies and extracting data using headless Chrome"""

    def __init__(self, delay_between_requests: float = 2.0, headless: bool = True):
        """Initialize ZaubaCorp client with headless Chrome"""
        self.base_url = "https://www.zaubacorp.com"
        self.delay = delay_between_requests
        self.headless = headless
        self.driver = None
        self._setup_driver()

        # Register cleanup on exit
        atexit.register(self.close)

    def _setup_driver(self):
        """Setup Chrome WebDriver with optimal settings"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument("--headless")

            # Essential arguments to avoid detection
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(
                "--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                'useAutomationExtension', False)

            # Set window size
            chrome_options.add_argument("--window-size=1920,1080")

            # Disable images and CSS for faster loading (optional)
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)

            # Additional stealth arguments
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-popup-blocking")

            # Set user agent
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            chrome_options.add_argument(f"--user-agent={user_agent}")

            # Setup service with ChromeDriverManager
            service = Service(ChromeDriverManager().install())

            # Create driver
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)

            # Execute script to remove webdriver property
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

        except Exception as e:
            raise ZaubaCorpError(f"Failed to setup Chrome driver: {str(e)}")

    def _wait_and_get_page_source(self, url: str, wait_element: str = None, timeout: int = 15) -> str:
        """Navigate to URL and get page source with optional element wait"""
        try:
            self.driver.get(url)

            if wait_element:
                try:
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, wait_element))
                    )
                except TimeoutException:
                    pass  # Continue anyway, maybe the content loaded

            # Small delay to ensure page is fully loaded
            time.sleep(1)

            return self.driver.page_source

        except WebDriverException as e:
            raise NetworkError(f"Failed to load page {url}: {str(e)}")

    def _search_companies_selenium(self, query: str, filter_type: SearchFilter = SearchFilter.COMPANY) -> Optional[str]:
        """Search using Selenium by posting to typeahead endpoint"""
        try:
            # First visit the main page to establish session
            self.driver.get(self.base_url)
            time.sleep(1)

            # Execute JavaScript to make the POST request
            script = f"""
            return fetch('{self.base_url}/typeahead', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'max-age=0',
                    'DNT': '1'
                }},
                body: 'search=' + encodeURIComponent(arguments[0]) + '&filter=' + arguments[1]
            }}).then(response => response.text());
            """

            result = self.driver.execute_async_script(f"""
            var callback = arguments[arguments.length - 1];
            fetch('{self.base_url}/typeahead', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                }},
                body: 'search={query}&filter={filter_type.value}'
            }})
            .then(response => response.text())
            .then(data => callback(data))
            .catch(error => callback(null));
            """)

            return result

        except Exception as e:
            print(f"Selenium search error: {e}")
            return None

    def search_companies(self,
                         query: str,
                         filter_type: SearchFilter = SearchFilter.COMPANY,
                         max_results: Optional[int] = None) -> List[CompanySearchResult]:
        """Search for companies using headless Chrome"""
        try:
            time.sleep(self.delay)

            response_text = self._search_companies_selenium(query, filter_type)

            if not response_text:
                raise NetworkError("Failed to get search results")

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

    def _fetch_html_selenium(self, company_id: str) -> Optional[str]:
        """Fetch HTML using Selenium"""
        try:
            url = f"{self.base_url}/{company_id}"
            return self._wait_and_get_page_source(url, wait_element="div.rc")
        except Exception:
            return None

    def get_company_data(self, company_id: str) -> CompanyData:
        """Get complete company data by company ID"""
        try:
            time.sleep(self.delay)

            html_content = self._fetch_html_selenium(company_id)
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

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage and testing
if __name__ == "__main__":
    # You can test the client like this:
    with ZaubaCorpClient(delay_between_requests=3.0) as client:
        try:
            # Search for companies
            results = client.search_companies("Reliance", max_results=3)
            print(f"Found {len(results)} companies")

            for result in results:
                print(f"- {result.name} ({result.id})")

                # Get detailed data for first result
                if result == results[0]:
                    company_data = client.get_company_data(result.id)
                    if company_data.success:
                        print(f"Successfully extracted data for {result.name}")
                        print(
                            f"Found {len(company_data.rc_sections)} sections")
                    else:
                        print(
                            f"Failed to extract data: {company_data.error_message}")

        except Exception as e:
            print(f"Error: {e}")
