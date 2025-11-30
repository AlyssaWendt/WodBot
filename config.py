import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio configuration
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
TWILIO_FROM = os.getenv('TWILIO_FROM')
MY_PHONE = os.getenv('MY_PHONE')

# CrossFit configuration
CROSSFIT_URL = os.getenv('CROSSFIT_URL', 'https://www.crossfit.com/wod')

# Scheduling configuration  
SEND_TIME = os.getenv('SEND_TIME', '07:00')

def validate_config():
    """Validate that all required configuration is present."""
    required_vars = [TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, MY_PHONE]
    missing = [name for name, value in zip(
        ['TWILIO_SID', 'TWILIO_TOKEN', 'TWILIO_FROM', 'MY_PHONE'], 
        required_vars
    ) if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True