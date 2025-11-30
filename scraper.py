import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from config import CROSSFIT_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_wod_html():
    """Fetch the HTML content from CrossFit WOD page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(CROSSFIT_URL, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully fetched WOD page: {CROSSFIT_URL}")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching WOD page: {e}")
        raise

def parse_wod(html):
    """Parse the WOD content from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        # Find the date (like "251130")
        date_elements = soup.find_all(['h1', 'h2'], string=lambda text: text and len(text) == 6 and text.isdigit())
        date_str = date_elements[0].get_text(strip=True) if date_elements else "Unknown Date"
        
        # Look for workout content - it's usually after "WORKOUT OF THE DAY" heading
        workout_content = ""
        
        # Find main workout section
        workout_sections = soup.find_all(string=lambda text: text and ("For time:" in text or "AMRAP" in text or "Rest Day" in text))
        
        if workout_sections:
            # Get the workout details
            for section in workout_sections:
                parent = section.parent
                if parent:
                    # Get text content from this section and surrounding elements
                    content_parts = []
                    current = parent
                    
                    # Look for the main workout text
                    while current:
                        text = current.get_text(strip=True) if hasattr(current, 'get_text') else str(current).strip()
                        if text and ("For time:" in text or "AMRAP" in text or "Rest Day" in text):
                            content_parts.append(text)
                            break
                        current = current.next_sibling
                    
                    if content_parts:
                        workout_content = "\n".join(content_parts)
                        break
        
        # If we couldn't find workout content, look for it in a different way
        if not workout_content:
            # Look for common workout patterns
            for element in soup.find_all(['p', 'div']):
                text = element.get_text(strip=True)
                if any(phrase in text for phrase in ["For time:", "AMRAP", "Rest Day", "rounds for time", "rounds of:"]):
                    workout_content = text
                    break
        
        # Check if it's a rest day
        rest_day = any(phrase in workout_content.lower() for phrase in ["rest day", "no workout"])
        
        # Format the parsed data
        parsed_wod = {
            "date": date_str,
            "formatted_date": format_date(date_str),
            "is_rest_day": rest_day,
            "workout": workout_content.strip() if workout_content else "Workout details not found",
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
            "raw_url": CROSSFIT_URL
        }

def format_date(date_str):
    """Convert date string like '251130' to '2025-11-30'."""
    try:
        if len(date_str) == 6 and date_str.isdigit():
            # Assuming format is YYMMDD
            year = "20" + date_str[:2]
            month = date_str[2:4]
            day = date_str[4:6]
            return f"{year}-{month}-{day}"
        else:
            return datetime.now().strftime("%Y-%m-%d")
    except:
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
            "raw_url": CROSSFIT_URL
        }

if __name__ == "__main__":
    # Test the scraper
    wod = get_todays_wod()
    print(f"Date: {wod['formatted_date']}")
    print(f"Rest Day: {wod['is_rest_day']}")
    print(f"Workout:\n{wod['workout']}")