"""
MTGTop8 URL-Based Scraper - Direct URL Input
No more dropdown headaches! Just provide the direct URL.
WITH COMPREHENSIVE LOGGING - CSV OUTPUT ONLY
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re
import logging
import sys
import traceback
from datetime import datetime

def setup_logging():
    """Setup simple, safe logging to both file and console"""
    # Create timestamp for log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"mtgtop8_scraper_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('MTGTop8Scraper')
    logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_filename

class MTGTop8URLScraper:
    def __init__(self):
        """Initialize the scraper with Chrome"""
        self.logger = logging.getLogger('MTGTop8Scraper')
        self.logger.info("🚀 Initializing MTGTop8 URL-Based Scraper...")
        self.logger.info("🔧 Using Chrome browser...")
        
        # Set up Chrome options for Windows x64
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, 15)
            
            self.all_events_data = []
            self.logger.info("✅ Chrome browser initialized successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Chrome: {e}")
            self.logger.error("💡 Make sure ChromeDriver is installed and in your PATH")
            self.logger.error("💡 Download from: https://chromedriver.chromium.org/downloads")
            raise
        
    def scrape_from_url(self, url, description=""):
        """Scrape events directly from a given URL - WITH PAGINATION SUPPORT"""
        self.logger.info(f"\n🎯 Scraping from URL: {description}")
        self.logger.info(f"🔗 URL: {url}")
        
        all_event_links = []
        current_page = 1
        
        try:
            # Navigate directly to the URL
            self.logger.info("🌐 Loading initial page...")
            self.driver.get(url)
            time.sleep(5)
            
            self.logger.info("✅ Initial page loaded successfully!")
            
            # Scrape all pages with pagination
            while True:
                self.logger.info(f"\n📄 Scraping page {current_page}...")
                
                # Extract events from current page
                page_events = self.get_event_links_from_current_page()
                
                if page_events:
                    self.logger.info(f"✅ Found {len(page_events)} events from SECOND Stable table on page {current_page}")
                    # Show first few events from this page
                    self.logger.debug("   📋 Sample events from SECOND Stable table:")
                    for i, event in enumerate(page_events[:3]):
                        self.logger.debug(f"      {i+1}. {event['name']}")
                    if len(page_events) > 3:
                        self.logger.debug(f"      ... and {len(page_events) - 3} more events")
                    
                    all_event_links.extend(page_events)
                else:
                    self.logger.warning(f"⚠️  No events found in SECOND Stable table on page {current_page}")
                    self.logger.debug("   🚫 STRICT MODE: Page skipped (need 2 Stable tables, using second one only)")
                    
                    # Debug what's actually on this page
                    self.logger.debug("   🔍 DEBUG: Checking page structure...")
                    stable_tables = self.driver.find_elements(By.CSS_SELECTOR, "table.Stable")
                    all_tables = self.driver.find_elements(By.TAG_NAME, "table")
                    self.logger.debug(f"      Total tables on page: {len(all_tables)}")
                    self.logger.debug(f"      Tables with class='Stable': {len(stable_tables)}")
                    
                    # Check page title and URL for context
                    page_title = self.driver.title
                    current_url = self.driver.current_url
                    self.logger.debug(f"      Page title: {page_title}")
                    self.logger.debug(f"      Current URL: {current_url}")
                    
                    # Show details about Stable tables found
                    if stable_tables:
                        self.logger.debug(f"      Stable tables analysis:")
                        for i, table in enumerate(stable_tables, 1):
                            all_links_in_table = table.find_elements(By.TAG_NAME, "a")
                            event_links_in_table = table.find_elements(By.CSS_SELECTOR, "a[href*='event?e=']")
                            status = "(USED)" if i == 2 else "(IGNORED)"
                            self.logger.debug(f"         Stable table #{i} {status}: {len(all_links_in_table)} total links, {len(event_links_in_table)} event links")

                # Look for "Next" button or next page number
                has_next_page = False
                
                self.logger.debug(f"🔍 Looking for pagination options on page {current_page}...")
                
                try:
                    # Method 1: Look for "Next" link - IMPROVED to look in Nav_norm divs
                    self.logger.debug("   📍 Method 1: Looking for 'Next' button in Nav_norm divs...")
                    
                    # First, find all Nav_norm divs
                    nav_divs = self.driver.find_elements(By.CSS_SELECTOR, "div.Nav_norm")
                    self.logger.debug(f"      Found {len(nav_divs)} div(s) with class='Nav_norm'")
                    
                    # Look for Next link in the LAST Nav_norm div (as you observed)
                    next_link = None
                    if nav_divs:
                        last_nav_div = nav_divs[-1]  # Get the last Nav_norm div
                        self.logger.debug(f"      Checking LAST Nav_norm div for 'Next' link...")
                        
                        # Look for Next link within this last Nav_norm div
                        next_links_in_div = last_nav_div.find_elements(By.XPATH, ".//a[contains(text(), 'Next') or contains(text(), 'next') or contains(text(), 'NEXT')]")
                        
                        if next_links_in_div:
                            next_link = next_links_in_div[0]
                            self.logger.debug(f"      Found 'Next' link in LAST Nav_norm div")
                        else:
                            self.logger.debug(f"      No 'Next' link found in LAST Nav_norm div")
                            # Debug: show what's actually in the last Nav_norm div
                            div_text = last_nav_div.text.strip()
                            self.logger.debug(f"      Last Nav_norm div content: '{div_text}'")
                    
                    if next_link:
                        next_class = next_link.get_attribute('class') or ""
                        next_href = next_link.get_attribute('href') or ""
                        self.logger.debug(f"      Next link text: '{next_link.text}', class: '{next_class}', enabled: {next_link.is_enabled()}")
                        self.logger.debug(f"      Next link URL: {next_href}")
                        
                        # Check for Nav_PN_no class - indicates no next page
                        if 'Nav_PN_no' in next_class:
                            self.logger.debug("      ❌ Next button has 'Nav_PN_no' class - no more pages available")
                        elif next_link.is_enabled():
                            self.logger.info(f"🔗 Clicking 'Next' button to go to page {current_page + 1}")
                            self.logger.info(f"   📍 Next button href URL: {next_href}")
                            self.driver.execute_script("arguments[0].click();", next_link)
                            time.sleep(4)
                            # Show actual URL after navigation
                            actual_url = self.driver.current_url
                            self.logger.info(f"   🎯 Actual navigated URL: {actual_url}")
                            has_next_page = True
                    else:
                        self.logger.debug("      No 'Next' link found in any Nav_norm div")
                    
                    # Method 2: If no "Next" button, try numbered pagination
                    if not has_next_page:
                        self.logger.debug("   📍 Method 2: Looking for numbered page links...")
                        next_page_num = current_page + 1
                        
                        # IMPROVED: More precise selectors to avoid false positives
                        page_selectors = [
                            # Look for exact number match that is the entire text content
                            f"//a[normalize-space(text())='{next_page_num}']",
                            # Look for links with cp= parameter in href
                            f"//a[contains(@href, 'cp={next_page_num}')]",
                            # Look for number in href parameter (most reliable)
                            f"//a[contains(@href, '&cp={next_page_num}') or contains(@href, '?cp={next_page_num}')]"
                        ]
                        
                        page_link_found = False
                        for i, selector in enumerate(page_selectors, 1):
                            page_links = self.driver.find_elements(By.XPATH, selector)
                            self.logger.debug(f"      Selector {i} '{selector}': found {len(page_links)} links")
                            
                            if page_links:
                                # Additional validation: make sure it's actually a pagination link
                                for page_link in page_links:
                                    link_text = page_link.text.strip()
                                    link_href = page_link.get_attribute('href') or ""
                                    link_class = page_link.get_attribute('class') or ""
                                    
                                    # FILTER 1: Skip if it has Nav_PN_no class (disabled pagination)
                                    if 'Nav_PN_no' in link_class:
                                        self.logger.debug(f"      Skipping disabled pagination link (Nav_PN_no): '{link_text}' → {link_href}")
                                        continue
                                    
                                    # Skip if it's clearly not a pagination link
                                    if ('archetype' in link_href or 
                                        'aggro' in link_text.lower() or
                                        'control' in link_text.lower() or
                                        'combo' in link_text.lower() or
                                        len(link_text) > 3):  # Page numbers should be short
                                        self.logger.debug(f"      Skipping non-pagination link: '{link_text}' → {link_href}")
                                        continue
                                    
                                    # This looks like a real pagination link
                                    self.logger.debug(f"      Valid page link found: '{link_text}' → {link_href}")
                                    self.logger.info(f"🔗 Clicking page {next_page_num} link...")
                                    self.logger.info(f"   📍 Page link href URL: {link_href}")
                                    self.driver.execute_script("arguments[0].click();", page_link)
                                    time.sleep(4)
                                    # Show actual URL after navigation
                                    actual_url = self.driver.current_url
                                    self.logger.info(f"   🎯 Actual navigated URL: {actual_url}")
                                    has_next_page = True
                                    page_link_found = True
                                    break
                            
                            if page_link_found:
                                break
                        
                        if not page_link_found:
                            self.logger.debug(f"      No valid page {next_page_num} link found")
                    
                    # Debug: Show all links on current page for troubleshooting
                    if not has_next_page:
                        self.logger.debug("   🔍 DEBUG: Showing potential pagination links:")
                        all_links = self.driver.find_elements(By.TAG_NAME, "a")
                        pagination_links = []
                        
                        for link in all_links:
                            href = link.get_attribute('href') or ""
                            text = link.text.strip()
                            link_class = link.get_attribute('class') or ""
                            
                            # Look for potential pagination links - IMPROVED FILTERING
                            is_pagination = False
                            
                            # Skip disabled pagination links first
                            if 'Nav_PN_no' in link_class:
                                continue
                            
                            # Check for explicit pagination patterns
                            if ('cp=' in href and 
                                'archetype' not in href and 
                                'event' not in href):
                                is_pagination = True
                            elif (text.lower() in ['next', 'prev', 'previous'] or
                                  (text.isdigit() and len(text) <= 2 and 
                                   'aggro' not in href.lower() and 
                                   'control' not in href.lower())):
                                is_pagination = True
                            
                            if is_pagination:
                                class_info = f" (class='{link_class}')" if link_class else ""
                                pagination_links.append(f"Text: '{text}' → {href}{class_info}")
                        
                        self.logger.debug(f"      Found {len(pagination_links)} potential pagination links:")
                        for i, link in enumerate(pagination_links[:10]):  # Show first 10
                            self.logger.debug(f"         {i+1}. {link}")
                        
                        if not pagination_links:
                            self.logger.debug("      No valid pagination links found - this might be the last page")
                except Exception as e:
                    self.logger.error(f"⚠️  Error checking for next page: {e}")
                    import traceback
                    self.logger.debug(traceback.format_exc())

                if not has_next_page:
                    self.logger.info(f"🏁 No more pages found. Scraped {current_page} page(s) total.")
                    break
                
                current_page += 1
                
                # Safety limit to prevent infinite loops - INCREASED for large datasets
                if current_page > 5000:
                    self.logger.warning("⚠️  Reached safety limit of 5000 pages")
                    break
            
            # Remove duplicates from all pages - OPTIMIZED for large datasets
            self.logger.info(f"🔄 Removing duplicates from {len(all_event_links)} total events...")
            unique_events = []
            seen_urls = set()
            
            for i, event in enumerate(all_event_links):
                if event['url'] not in seen_urls:
                    unique_events.append(event)
                    seen_urls.add(event['url'])
                
                # Progress indicator for large datasets
                if i > 0 and i % 1000 == 0:
                    self.logger.debug(f"   Processed {i:,} events for deduplication...")
            
            self.logger.info(f"\n📊 PAGINATION SUMMARY (STRICT MODE - SECOND Stable table only):")
            self.logger.info(f"   • Pages scraped: {current_page}")
            self.logger.info(f"   • Total events found: {len(all_event_links):,} (from SECOND Stable table only)")
            self.logger.info(f"   • Unique events: {len(unique_events):,}")
            self.logger.info(f"   • Duplicates removed: {len(all_event_links) - len(unique_events):,}")
            
            if len(all_event_links) == 0:
                self.logger.warning("⚠️  No events found in any SECOND Stable tables across all pages")
                self.logger.warning("🚫 STRICT MODE: Only looking in SECOND table.Stable - ignoring first table")
                return 0
                
            # Process all events found
            events_to_process = unique_events  # Process all events from all pages
            self.logger.info(f"\n📈 Processing all {len(events_to_process):,} events from all pages...")
            
            # Add progress tracking for large datasets
            total_events = len(events_to_process)
            if total_events > 1000:
                self.logger.info(f"🕐 Large dataset detected ({total_events:,} events)")
                self.logger.info(f"⏱️  Estimated time: {(total_events * 6) / 60:.1f} minutes")
            
            events_processed = 0
            for i, event in enumerate(events_to_process, 1):
                # Progress reporting for large datasets
                if total_events > 100 and i % 50 == 0:
                    progress = (i / total_events) * 100
                    self.logger.info(f"📊 Progress: {i:,}/{total_events:,} events ({progress:.1f}%)")
                
                self.logger.info(f"\n--- Event {i:,}/{len(events_to_process):,} ---")
                
                event_data = self.extract_event_data(event['url'], event['name'])
                
                if event_data:
                    self.all_events_data.append(event_data)
                    events_processed += 1
                    self.logger.info(f"✅ Event {i:,} completed successfully")
                else:
                    self.logger.warning(f"❌ Event {i:,} failed")
                    
                # Be respectful to the server - adjust delay for large datasets
                if i < len(events_to_process):
                    if total_events > 10000:
                        # Shorter delay for very large datasets to reduce total time
                        self.logger.debug("⏳ Waiting 2 seconds...")
                        time.sleep(2)
                    else:
                        self.logger.debug("⏳ Waiting 3 seconds...")
                        time.sleep(3)
            
            return events_processed
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping URL: {e}")
            self.logger.debug(traceback.format_exc())
            return 0
            
    def get_event_links_from_current_page(self):
        """Get event links from the current page only - STRICT: ONLY from SECOND table.Stable"""
        event_links = []
        
        try:
            # Scroll to make sure page is fully loaded
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Look for events ONLY in the SECOND table with class="Stable"
            stable_tables = self.driver.find_elements(By.CSS_SELECTOR, "table.Stable")
            self.logger.debug(f"Found {len(stable_tables)} table(s) with class='Stable'")
            
            if len(stable_tables) < 2:
                self.logger.warning(f"⚠️  Expected 2 Stable tables, found {len(stable_tables)} - SKIPPING PAGE")
                self.logger.debug("   🚫 STRICT MODE: Need exactly 2 Stable tables to get data from second one")
                return []  # Return empty list - skip this page entirely
            
            # Get events from ONLY the second Stable table (index 1)
            second_table = stable_tables[1]
            event_elements = second_table.find_elements(By.CSS_SELECTOR, "a[href*='event?e=']")
            self.logger.debug(f"   Found {len(event_elements)} event links in SECOND Stable table")
            
            # Debug: Show what's in first table vs second table
            first_table_events = stable_tables[0].find_elements(By.CSS_SELECTOR, "a[href*='event?e=']")
            self.logger.debug(f"   First Stable table has {len(first_table_events)} event links (IGNORED)")
            self.logger.debug(f"   Second Stable table has {len(event_elements)} event links (USED)")
            
            filtered_count = 0
            for element in event_elements:
                try:
                    event_text = element.text.strip()
                    event_url = element.get_attribute('href')
                    element_class = element.get_attribute('class') or ""
                    
                    # Skip empty or invalid links
                    if not event_text or not event_url:
                        continue
                        
                    # FILTER 1: Skip events with class="und"
                    if 'und' in element_class:
                        self.logger.debug(f"Skipping event with class='und': {event_text}")
                        filtered_count += 1
                        continue
                        
                    # FILTER 2: Skip League events (case insensitive)
                    if 'league' in event_text.lower():
                        self.logger.debug(f"Skipping League event: {event_text}")
                        filtered_count += 1
                        continue
                        
                    # Add to list (duplicates will be removed later)
                    event_links.append({
                        'name': event_text,
                        'url': event_url
                    })
                        
                except Exception as e:
                    continue
            
            self.logger.debug(f"Filtered out {filtered_count} events (und class + league events)")
            self.logger.debug(f"Remaining valid events from SECOND Stable table: {len(event_links)}")
            
            return event_links
            
        except Exception as e:
            self.logger.error(f"❌ Error getting events from SECOND Stable table: {e}")
            return []
            
    def extract_event_data(self, event_url, event_name):
        """Extract data from individual event"""
        self.logger.info(f"📊 Processing: {event_name[:50]}...")
        
        try:
            # Navigate to event page
            self.driver.get(event_url)
            time.sleep(3)
            
            # Extract date
            date = "Unknown"
            try:
                page_source = self.driver.page_source
                date_match = re.search(r'\d{2}/\d{2}/\d{2}', page_source)
                if date_match:
                    date = date_match.group()
            except:
                pass
            
            # Extract deck information
            decks = []
            try:
                # Look for deck links in the page
                deck_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='&d=']")
                
                position_counter = 1
                for link in deck_links:
                    try:
                        deck_name = link.text.strip()
                        deck_url = link.get_attribute('href')
                        
                        if deck_name and deck_url and '&d=' in deck_url:
                            decks.append({
                                'position': position_counter,
                                'deck_name': deck_name,
                                'player': 'Unknown',  # Can be improved later
                                'deck_url': deck_url
                            })
                            position_counter += 1
                            
                    except:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"⚠️  Could not extract all deck data: {e}")
            
            event_data = {
                'event_name': event_name,
                'date': date,
                'event_url': event_url,
                'total_decks': len(decks),
                'decks': decks
            }
            
            self.logger.info(f"✅ Extracted {len(decks)} decks")
            return event_data
            
        except Exception as e:
            self.logger.error(f"❌ Error processing event: {e}")
            return None
            
    def save_data(self):
        """Save all extracted data to CSV file only - OPTIMIZED for large datasets"""
        if not self.all_events_data:
            self.logger.warning("❌ No data to save")
            return
            
        self.logger.info(f"\n💾 Saving data from {len(self.all_events_data):,} events...")
        
        # Create flat list for CSV - with progress tracking for large datasets
        all_decks = []
        total_events = len(self.all_events_data)
        
        for event_idx, event in enumerate(self.all_events_data):
            # Progress indicator for large datasets
            if total_events > 1000 and event_idx % 500 == 0 and event_idx > 0:
                self.logger.debug(f"   Processing event {event_idx:,}/{total_events:,} for CSV...")
            
            for deck in event['decks']:
                all_decks.append({
                    'event_name': event['event_name'],
                    'event_date': event['date'],
                    'event_url': event['event_url'],
                    'deck_position': deck['position'],
                    'deck_name': deck['deck_name'],
                    'player_name': deck['player'],
                    'deck_url': deck['deck_url']
                })
        
        # Save to CSV (Excel-friendly) with chunking for very large datasets
        if all_decks:
            self.logger.info(f"💾 Writing {len(all_decks):,} decks to CSV...")
            
            df = pd.DataFrame(all_decks)
            csv_filename = 'mtgtop8_decks.csv'
            
            # For very large datasets, use chunking to avoid memory issues
            if len(all_decks) > 100000:
                self.logger.info("🔄 Large dataset detected - using chunked CSV writing...")
                chunk_size = 10000
                for i in range(0, len(df), chunk_size):
                    chunk = df[i:i+chunk_size]
                    if i == 0:
                        chunk.to_csv(csv_filename, index=False, mode='w', header=True)
                    else:
                        chunk.to_csv(csv_filename, index=False, mode='a', header=False)
                    self.logger.debug(f"   Written chunk {i//chunk_size + 1} ({i+len(chunk):,}/{len(df):,} rows)")
            else:
                df.to_csv(csv_filename, index=False)
            
            self.logger.info(f"✅ Deck data saved to '{csv_filename}'")
            self.logger.info(f"📊 Total decks extracted: {len(all_decks):,}")
        
        # Print summary with better formatting for large numbers
        self.logger.info(f"\n📈 EXTRACTION SUMMARY:")
        self.logger.info(f"   • Total Events: {len(self.all_events_data):,}")
        self.logger.info(f"   • Total Decks: {len(all_decks):,}")
        self.logger.info(f"   • File Created: {csv_filename}")
        
        # Memory usage info for large datasets
        if len(all_decks) > 50000:
            file_size_mb = sum(len(str(deck)) for deck in all_decks) / (1024 * 1024)
            self.logger.info(f"   • Estimated file size: {file_size_mb:.1f} MB")
        
    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
            self.logger.info("🏁 Browser closed successfully")
        except:
            self.logger.info("🏁 Browser was already closed")

def main():
    """Main function - URL-based scraping with safe logging"""
    
    import sys
    import traceback
    
    # Setup simple, safe logging
    logger, log_filename = setup_logging()
    
    try:
        logger.info("🚀 MTGTop8 URL-Based Scraper for Windows 11 x64")
        logger.info("🔗 Command Line Version - Pass URLs as arguments!")
        logger.info(f"📝 Logging to file: {log_filename}")
        logger.info("=" * 60)
        
        # Log system information
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Command line args: {sys.argv}")
        
        # Check if URL was provided as command line argument
        if len(sys.argv) > 1:
            # URLs provided as command line arguments
            urls_to_scrape = []
            for i, url in enumerate(sys.argv[1:], 1):
                urls_to_scrape.append({
                    "url": url,
                    "description": f"URL {i}"
                })
            logger.info(f"📋 Processing {len(urls_to_scrape)} URL(s) from command line:")
            for i, url_info in enumerate(urls_to_scrape, 1):
                logger.info(f"   {i}. {url_info['url']}")
        else:
            # No command line arguments - use default
            logger.info("💡 No URL provided. Using default Standard URL.")
            logger.info("💡 Next time, run like this:")
            logger.info("   python mtgtop8_url_scraper.py \"https://www.mtgtop8.com/format?f=ST\"")
            logger.info("")
            
            urls_to_scrape = [
                {
                    "url": "https://www.mtgtop8.com/format?f=ST",
                    "description": "Standard - Default View"
                }
            ]
        
        start_time = time.time()
        
        # Initialize scraper
        try:
            logger.info("🔧 Initializing browser...")
            logger.debug("Setting up Chrome options for Windows x64...")
            scraper = MTGTop8URLScraper()
        except Exception as e:
            logger.error(f"❌ FAILED TO START: {e}")
            logger.debug(f"Browser initialization error: {traceback.format_exc()}")
            input("Press Enter to close...")
            return
        
        try:
            logger.info(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
            
            # Process each URL
            total_events_processed = 0
            for i, url_info in enumerate(urls_to_scrape, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"📄 URL {i}/{len(urls_to_scrape)}: {url_info['description']}")
                logger.info(f"{'='*60}")
                
                logger.debug(f"Starting to process URL: {url_info['url']}")
                
                events_processed = scraper.scrape_from_url(
                    url_info['url'], 
                    url_info['description']
                )
                total_events_processed += events_processed
                
                logger.info(f"\n✅ URL {i} completed: {events_processed} events processed")
                logger.debug(f"Total events processed so far: {total_events_processed}")
                
            # Save all collected data
            logger.info(f"\n{'='*60}")
            logger.info("💾 SAVING DATA...")
            logger.debug("Starting data save process...")
            scraper.save_data()
            
            # Final summary
            total_time = time.time() - start_time
            logger.info(f"\n🎉 SCRAPING COMPLETED SUCCESSFULLY!")
            logger.info(f"⏰ Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
            logger.info(f"📊 Total events processed: {total_events_processed}")
            logger.info(f"🕐 Completed at: {time.strftime('%H:%M:%S')}")
            logger.info(f"📝 Complete log saved to: {log_filename}")
            
        except KeyboardInterrupt:
            logger.warning(f"\n⏹️  SCRAPING INTERRUPTED BY USER (Ctrl+C)")
            logger.debug("User interrupted with Ctrl+C")
            if hasattr(scraper, 'all_events_data') and scraper.all_events_data:
                logger.info("💾 Saving partial data...")
                scraper.save_data()
        except Exception as e:
            logger.error(f"\n❌ UNEXPECTED ERROR: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.debug(f"Full error traceback: {traceback.format_exc()}")
            if hasattr(scraper, 'all_events_data') and scraper.all_events_data:
                logger.info("💾 Saving partial data...")
                try:
                    scraper.save_data()
                except Exception as save_error:
                    logger.error(f"❌ Error saving partial data: {save_error}")
        finally:
            logger.debug("Cleaning up...")
            try:
                scraper.close()
            except Exception as close_error:
                logger.error(f"Error closing scraper: {close_error}")
            
            logger.info(f"\n🏁 Script finished.")
            logger.info(f"📝 Complete log saved to: {log_filename}")
    
    except Exception as e:
        # Catch any logging setup errors
        print(f"❌ CRITICAL ERROR in main setup: {e}")
        print(traceback.format_exc())
    
    finally:
        print(f"\n📝 Log file: {log_filename}")
        input("Press Enter to close...")

if __name__ == "__main__":
    main()