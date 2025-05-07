import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Optional
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BaseAgent:
    """Base agent class with common functionality for all e-commerce agents"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]

    def setup_selenium_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        }


class AmazonAgent(BaseAgent):
    """Agent specifically designed for Amazon product searches"""
    
    async def search_products(self, search_query: str) -> List[Dict]:
        """Search for products on Amazon"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_products_sync, search_query)
        
    def _search_products_sync(self, search_query: str) -> List[Dict]:
        """Synchronous version of Amazon scraper to be run in a thread via run_in_executor"""
        driver = self.setup_selenium_driver()
        products = []
        
        try:
            print("Accessing Amazon...")
            driver.get(f"https://www.amazon.in/s?k={search_query.replace(' ', '+')}")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Give the page time to fully load
            time.sleep(3)
            
            # Scroll to load more products
            print("Scrolling page...")
            for _ in range(2):
                driver.execute_script("window.scrollTo(0, window.scrollY + 800)")
                time.sleep(1.5)
            
            # Parse products
            print("Parsing Amazon products...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Multiple selector patterns for product containers
            item_selectors = [
                'div.s-result-item[data-component-type="s-search-result"]',
                'div.sg-col-4-of-12',
                'div.s-asin',
                'div[data-asin]:not([data-asin=""])'
            ]
            
            # Try each selector pattern until we find products
            items = []
            for selector in item_selectors:
                items = soup.select(selector)
                if items:
                    print(f"Found {len(items)} products using selector: {selector}")
                    break
            
            for item in items[:5]:  # Get first 5 products
                try:
                    # Multiple selector patterns for each field
                    name_selectors = [
                        'h2 .a-link-normal',
                        'h2 span.a-text-normal',
                        '.a-size-medium.a-text-normal',
                        '[data-cy="title-recipe"]',
                        'h2 a span',
                        '.a-size-base-plus.a-color-base.a-text-normal'
                    ]
                    
                    price_selectors = [
                        '.a-price .a-offscreen',
                        '.a-price-whole',
                        'span.a-price',
                        '[data-cy="price-recipe"]',
                        'span.a-color-base span.a-color-price'
                    ]
                    
                    rating_selectors = [
                        '.a-icon-star-small .a-icon-alt',
                        '.a-icon-star .a-icon-alt',
                        '[data-cy="rating-recipe"]',
                        'i.a-icon.a-icon-star-small span',
                        'i.a-icon.a-icon-star span'
                    ]
                    
                    review_selectors = [
                        'span[aria-label*="stars"] + span',
                        '.a-size-base.s-underline-text',
                        '[data-cy="review-count-recipe"]'
                    ]
                    
                    # Try different selectors for each field
                    name = None
                    for selector in name_selectors:
                        name_elem = item.select_one(selector)
                        if name_elem:
                            name = name_elem.text.strip()
                            break
                    
                    price = None
                    for selector in price_selectors:
                        price_elem = item.select_one(selector)
                        if price_elem:
                            price = price_elem.text.strip()
                            break
                    
                    rating = None
                    for selector in rating_selectors:
                        rating_elem = item.select_one(selector)
                        if rating_elem:
                            rating = rating_elem.text.strip()
                            break
                    
                    reviews = None
                    for selector in review_selectors:
                        reviews_elem = item.select_one(selector)
                        if reviews_elem:
                            reviews = reviews_elem.text.strip()
                            break
                    
                    # Only add products with at least a name
                    if name:
                        print(f"Found Amazon product: {name[:50]}...")
                        products.append({
                            'name': name,
                            'price': price if price else "Not available",
                            'rating': rating if rating else "No rating",
                            'reviews': reviews if reviews else "No reviews",
                            'source': 'Amazon'
                        })
                except Exception as e:
                    print(f"Error parsing individual Amazon product: {str(e)}")
                    continue
                    
        finally:
            driver.quit()
            
        return products


class FlipkartAgent(BaseAgent):
    """Agent specifically designed for Flipkart product searches"""
    
    async def search_products(self, search_query: str) -> List[Dict]:
        """Scrape Flipkart products using direct HTTP requests"""
        products = []
        
        try:
            print("Accessing Flipkart using direct HTTP request...")
            
            # Format the search URL
            search_url = f"https://www.flipkart.com/search?q={search_query.replace(' ', '+')}"
            
            # Create a session with custom headers to mimic a browser
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'TE': 'trailers'
            }
            
            # Make the HTTP request
            async with aiohttp.ClientSession() as session:
                print(f"Sending request to: {search_url}")
                async with session.get(search_url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        print("Successfully received response from Flipkart")
                        html_content = await response.text()
                        
                        # Parse the HTML
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Save the HTML for debugging (optional)
                        with open("flipkart_direct_response.html", "w", encoding="utf-8") as f:
                            f.write(html_content)
                        
                        # Multiple selector patterns for product containers
                        item_selectors = [
                            'div._1YokD2._3Mn1Gg div._1AtVbE',
                            'div._4ddWXP',
                            'div._2kHMtA',
                            'div.CXW8mj',
                            'div._1xHGtK._373qXS',
                            'div[data-id]'
                        ]
                        
                        # Try each selector until we find products
                        items = []
                        for selector in item_selectors:
                            items = soup.select(selector)
                            if items and len(items) > 2:  # Ensure we have actual products (more than just headers)
                                print(f"Found {len(items)} products using selector: {selector}")
                                break
                        
                        # If standard selectors fail, try looking for typical product patterns
                        if not items or len(items) <= 2:
                            print("Standard selectors didn't work, trying alternative approach...")
                            
                            # Look for elements with price class
                            price_elements = soup.select('div._30jeq3')
                            
                            if price_elements:
                                print(f"Found {len(price_elements)} price elements, using parent elements as products")
                                
                                # For each price, get its parent or grandparent as a product container
                                for price_elem in price_elements[:10]:  # Limit to first 10
                                    # Navigate up to potential product container
                                    parent = price_elem.parent
                                    grandparent = parent.parent if parent else None
                                    great_grandparent = grandparent.parent if grandparent else None
                                    
                                    # Choose the most likely product container
                                    product_container = None
                                    for container in [great_grandparent, grandparent, parent]:
                                        if container and len(container.get_text(strip=True)) > 20:
                                            product_container = container
                                            break
                                    
                                    if product_container:
                                        items.append(product_container)
                        
                        # Process products
                        for item in items[:5]:  # Get first 5 products
                            try:
                                # Extract product information using various selectors
                                name_selectors = [
                                    'div._4rR01T', 'a.s1Q9rs', 'a.IRpwTa', '._2WkVRV',
                                    '.B_NuCI', '.Bv11UC', 'a[title]'
                                ]
                                
                                price_selectors = [
                                    'div._30jeq3', 'div._3I9_wc', '._25b18c',
                                    '._30jeq3._1_WHN1', '.PEDQHg'
                                ]
                                
                                rating_selectors = [
                                    'div._3LWZlK', 'div.gUuXy-', '.hGSR34',
                                    '._1lRcqv ._3LWZlK', 'span[id*="productRating"]'
                                ]
                                
                                review_selectors = [
                                    'span._2_R_DZ', 'span._13vcmD', '._1lRcqv',
                                    'span[class*="review"]', '._2_R_DZ span'
                                ]
                                
                                # Extract data using selectors
                                name = None
                                for selector in name_selectors:
                                    name_elem = item.select_one(selector)
                                    if name_elem:
                                        name = name_elem.text.strip()
                                        break
                                
                                price = None
                                for selector in price_selectors:
                                    price_elem = item.select_one(selector)
                                    if price_elem:
                                        price = price_elem.text.strip()
                                        break
                                
                                rating = None
                                for selector in rating_selectors:
                                    rating_elem = item.select_one(selector)
                                    if rating_elem:
                                        rating = rating_elem.text.strip()
                                        break
                                
                                reviews = None
                                for selector in review_selectors:
                                    reviews_elem = item.select_one(selector)
                                    if reviews_elem:
                                        reviews = reviews_elem.text.strip()
                                        break
                                
                                # Extract link if available
                                link = None
                                link_elem = item.select_one('a[href]')
                                if link_elem and 'href' in link_elem.attrs:
                                    link = 'https://www.flipkart.com' + link_elem['href'] if not link_elem['href'].startswith('http') else link_elem['href']
                                
                                # Extract image if available
                                image = None
                                img_elem = item.select_one('img[src]')
                                if img_elem and 'src' in img_elem.attrs:
                                    image = img_elem['src']
                                
                                # Fall back to raw text if structured extraction fails
                                if not name and not price:
                                    all_text = item.get_text(separator=' ', strip=True)
                                    if all_text:
                                        # Use raw text and try to identify price pattern
                                        name = all_text[:100] + "..." if len(all_text) > 100 else all_text
                                        # Look for price pattern (₹ followed by digits)
                                        import re
                                        price_match = re.search(r'₹[\d,]+', all_text)
                                        price = price_match.group(0) if price_match else "Not identified"
                                
                                # Only add products with at least some information
                                if name or price:
                                    print(f"Found Flipkart product: {name[:50] if name else 'Unknown'}...")
                                    products.append({
                                        'name': name if name else "Unknown Product",
                                        'price': price if price else "Not available",
                                        'rating': f"{rating} stars" if rating else "No rating",
                                        'reviews': reviews if reviews else "No reviews",
                                        'source': 'Flipkart',
                                        'link': link,
                                        'image': image
                                    })
                            except Exception as e:
                                print(f"Error parsing individual Flipkart product: {str(e)}")
                                continue
                    else:
                        print(f"Failed to get Flipkart search results. Status code: {response.status}")
                        
        except Exception as e:
            print(f"Error during Flipkart HTTP request: {str(e)}")
            
        return products


class EcommerceAgent:
    """Combined agent that searches across multiple e-commerce platforms"""
    
    def __init__(self):
        self.amazon_agent = AmazonAgent()
        self.flipkart_agent = FlipkartAgent()

    async def search_all_products(self, query: str) -> Dict:
        # Run both scrapers concurrently
        amazon_task = self.amazon_agent.search_products(query)
        flipkart_task = self.flipkart_agent.search_products(query)
        
        # Wait for both tasks to complete
        amazon_products, flipkart_products = await asyncio.gather(amazon_task, flipkart_task)
        
        print(f"Found {len(amazon_products)} Amazon products")
        print(f"Found {len(flipkart_products)} Flipkart products")

        # Combine results
        all_products = amazon_products + flipkart_products
        
        return {
            "query": query,
            "products": all_products,
            "total_found": len(all_products),
            "amazon_count": len(amazon_products),
            "flipkart_count": len(flipkart_products)
        }


# Example usage for each agent type
async def main():
    # Get command line arguments to select which agent to use
    import sys
    agent_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    while True:
        query = input("\nEnter product to search (or 'quit' to exit): ").strip()
        if query.lower() == 'quit':
            break
            
        if not query:
            print("Please enter a valid search query")
            continue
            
        print(f"\nSearching for: {query}")
        print("This may take a few moments...")
        
        if agent_type == "amazon":
            # Amazon only search
            amazon_agent = AmazonAgent()
            products = await amazon_agent.search_products(query)
            print(f"\nFound {len(products)} products on Amazon:")
            if products:
                print(json.dumps(products, indent=2, ensure_ascii=False))
            else:
                print("No products found. Please try again with different search terms.")
                
        elif agent_type == "flipkart":
            # Flipkart only search
            flipkart_agent = FlipkartAgent()
            products = await flipkart_agent.search_products(query)
            print(f"\nFound {len(products)} products on Flipkart:")
            if products:
                print(json.dumps(products, indent=2, ensure_ascii=False))
            else:
                print("No products found. Please try again with different search terms.")
                
        else:
            # Search both platforms
            ecommerce_agent = EcommerceAgent()
            results = await ecommerce_agent.search_all_products(query)
            
            if results["total_found"] == 0:
                print("\nNo products found. Please try again with different search terms.")
            else:
                print(f"\nFound {results['amazon_count']} products on Amazon and {results['flipkart_count']} products on Flipkart:")
                print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())