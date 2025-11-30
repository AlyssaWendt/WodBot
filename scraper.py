import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import time
from config import CROSSFIT_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_wod_html(max_retries=3, delay=1):
    """Fetch the HTML content from CrossFit WOD page with retry logic."""
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(CROSSFIT_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Basic content validation
            if len(response.text) < 1000:
                logger.warning(f"Response seems too short ({len(response.text)} chars), might be blocked")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                    continue
            
            logger.info(f"Successfully fetched WOD page: {CROSSFIT_URL}")
            return response.text
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
    
    # If we get here, all retries failed
    logger.error(f"Failed to fetch WOD page after {max_retries} attempts")
    raise requests.exceptions.RequestException(f"Failed after {max_retries} retries")

def parse_wod(html):
    """Parse the WOD content from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        # Find the date (like "251130")
        date_elements = soup.find_all(['h1', 'h2'], string=lambda text: text and len(text) == 6 and text.isdigit())
        date_str = date_elements[0].get_text(strip=True) if date_elements else "Unknown Date"
        
        # Look for workout content - it's usually after "WORKOUT OF THE DAY" heading
        workout_content = ""
        
        # Expanded workout patterns to catch more variations
        workout_patterns = [
            "For time:", "AMRAP", "Rest Day", "Recovery Day", "Active Recovery",
            "rounds for time", "rounds of:", "EMOM", "Tabata", "Every minute on the minute",
            "As many rounds as possible", "As many reps as possible", "Death by",
            "For load:", "Heavy single", "Work up to", "Find your"
        ]
        
        # Find main workout section with better content extraction
        workout_sections = soup.find_all(string=lambda text: text and any(pattern.lower() in text.lower() for pattern in workout_patterns))
        
        if workout_sections:
            # Get the workout details - try to get full workout content
            for section in workout_sections:
                parent = section.parent
                if parent:
                    # Try to get the full workout content from parent elements
                    current = parent
                    content_parts = []
                    
                    # Look for container with full workout
                    while current and len(content_parts) < 10:  # Prevent infinite loops
                        text = current.get_text(strip=True) if hasattr(current, 'get_text') else str(current).strip()
                        if text and any(pattern.lower() in text.lower() for pattern in workout_patterns):
                            # Try to get more complete content
                            if hasattr(current, 'get_text'):
                                full_text = current.get_text(separator='\n', strip=True)
                                if len(full_text) > len(text):
                                    content_parts.append(full_text)
                                else:
                                    content_parts.append(text)
                            else:
                                content_parts.append(text)
                            break
                        current = current.next_sibling
                    
                    if content_parts:
                        workout_content = "\n".join(content_parts)
                        break
        
        # If we couldn't find workout content, look for it in a different way
        if not workout_content:
            # Look for common workout patterns in various elements
            for element in soup.find_all(['p', 'div', 'section', 'article']):
                text = element.get_text(strip=True)
                if any(pattern.lower() in text.lower() for pattern in workout_patterns):
                    # Try to get more complete workout text
                    full_text = element.get_text(separator='\n', strip=True)
                    workout_content = full_text if len(full_text) > len(text) else text
                    break
        
        # Check if it's a rest day - improved pattern matching
        rest_patterns = [
            "rest day", "no workout", "recovery day", "active recovery",
            "take a rest", "day off", "recovery", "mobility day"
        ]
        rest_day = any(pattern in workout_content.lower() for pattern in rest_patterns) if workout_content else False
        
        # Additional check: if workout content is very short and contains rest-like words
        if not rest_day and workout_content and len(workout_content.strip()) < 50:
            rest_day = any(word in workout_content.lower() for word in ["rest", "recovery", "off"])
        
        # Look for scaled/beginner versions
        scaled_content = ""
        scaled_patterns = ["scaled", "beginner", "intermediate", "modified", "scaling", "substitute"]
        
        # Search for scaled workout content
        for element in soup.find_all(['p', 'div', 'section', 'li']):
            text = element.get_text(strip=True)
            if any(pattern.lower() in text.lower() for pattern in scaled_patterns):
                # Check if this looks like actual workout content (not just navigation/headers)
                if any(workout_word in text.lower() for workout_word in ["rounds", "reps", "time", "weight", "distance", "substitute", "modify"]):
                    if len(text) > 20:  # Avoid short headers
                        scaled_content += f"\n{text}"
        
        # Format the parsed data with scaled options
        parsed_wod = {
            "date": date_str,
            "formatted_date": format_date(date_str),
            "is_rest_day": rest_day,
            "workout": workout_content.strip() if workout_content else "Workout details not found",
            "scaled_options": scaled_content.strip() if scaled_content else None,
            "raw_url": CROSSFIT_URL
        }
        
        logger.info(f"Successfully parsed WOD for {parsed_wod['formatted_date']}")
        return parsed_wod
        
    except Exception as e:
        logger.error(f"Error parsing WOD content: {e}")
        return {
            "date": "Error",
            "formatted_date": datetime.now().strftime("%Y-%m-%d"),
            "is_rest_day": False,
            "workout": f"Error parsing workout: {str(e)}",
            "scaled_options": None,
            "raw_url": CROSSFIT_URL
        }

def format_date(date_str):
    """Convert date string like '251130' to '2025-11-30'."""
    try:
        if len(date_str) == 6 and date_str.isdigit():
            # Assuming format is YYMMDD
            year_2digit = int(date_str[:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            
            # Handle century rollover (assume 2000-2099 for now)
            # Could be improved with logic like: if year < 50: 2000+year else 1900+year
            year = 2000 + year_2digit if year_2digit < 100 else year_2digit
            
            # Validate date ranges
            if not (1 <= month <= 12 and 1 <= day <= 31):
                logger.warning(f"Invalid date components: month={month}, day={day}")
                return datetime.now().strftime("%Y-%m-%d")
            
            # Try to create actual date to validate (catches Feb 30, etc.)
            try:
                datetime(year, month, day)
                return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError as e:
                logger.warning(f"Invalid date {year}-{month}-{day}: {e}")
                return datetime.now().strftime("%Y-%m-%d")
        else:
            return datetime.now().strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Date formatting error: {e}")
        return datetime.now().strftime("%Y-%m-%d")

def get_todays_wod():
    """Main function to get today's WOD."""
    try:
        html = fetch_wod_html()
        wod = parse_wod(html)
        return wod
    except Exception as e:
        logger.error(f"Failed to get today's WOD: {e}")
        # Return a fallback WOD
        return {
            "date": "Error",
            "formatted_date": datetime.now().strftime("%Y-%m-%d"),
            "is_rest_day": False,
            "workout": "Unable to fetch today's WOD. Try this fallback: 5 rounds of 400m run, 20 air squats, 10 push-ups.",
            "scaled_options": "Scaled: 3 rounds of 200m walk, 15 air squats, 5 knee push-ups.",
            "raw_url": CROSSFIT_URL
        }

if __name__ == "__main__":
    # Test the scraper
    wod = get_todays_wod()
    print(f"Date: {wod['formatted_date']}")
    print(f"Rest Day: {wod['is_rest_day']}")
    print(f"Workout:\n{wod['workout']}")
    
    if wod.get('scaled_options'):
        print(f"\nScaled Options:\n{wod['scaled_options']}")
    else:
        print("\nNo scaled options found")