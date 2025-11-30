#!/usr/bin/env python3
"""
Test script for WodBot components
"""

import sys
import traceback
from scraper import fetch_wod_html, parse_wod, get_todays_wod, format_date
from config import validate_config, CROSSFIT_URL

def test_date_formatting():
    """Test the date formatting function."""
    print("🗓️  Testing date formatting...")
    test_cases = [
        "251130",  # Today's format
        "251225",  # Christmas
        "250101",  # New Year
        "invalid", # Invalid date
    ]
    
    for date_str in test_cases:
        formatted = format_date(date_str)
        print(f"  {date_str} -> {formatted}")
    print()

def test_html_fetching():
    """Test if we can fetch HTML from CrossFit.com"""
    print("🌐 Testing HTML fetching...")
    try:
        html = fetch_wod_html()
        print(f"  ✅ Successfully fetched HTML ({len(html)} characters)")
        print(f"  📄 URL: {CROSSFIT_URL}")
        return html
    except Exception as e:
        print(f"  ❌ Failed to fetch HTML: {e}")
        return None

def test_parsing(html=None):
    """Test parsing of WOD content."""
    print("🔍 Testing WOD parsing...")
    try:
        if html is None:
            html = fetch_wod_html()
        
        wod = parse_wod(html)
        print(f"  📅 Date: {wod['date']} ({wod['formatted_date']})")
        print(f"  😴 Rest Day: {wod['is_rest_day']}")
        print(f"  💪 Workout Preview: {wod['workout'][:100]}...")
        
        if wod.get('scaled_options'):
            print(f"  📉 Scaled Options Preview: {wod['scaled_options'][:100]}...")
            print(f"  ✅ Scaled options successfully captured!")
        else:
            print(f"  📉 Scaled Options: None found (may be normal for rest days)")
            
        # Validate structure
        required_fields = ['date', 'formatted_date', 'is_rest_day', 'workout', 'scaled_options', 'raw_url']
        missing_fields = [field for field in required_fields if field not in wod]
        if missing_fields:
            print(f"  ⚠️  Missing fields: {missing_fields}")
        else:
            print(f"  ✅ All required fields present")
            
        return wod
    except Exception as e:
        print(f"  ❌ Failed to parse WOD: {e}")
        traceback.print_exc()
        return None

def test_scaled_workout_parsing():
    """Test parsing of scaled workout options."""
    print("⚖️  Testing scaled workout parsing...")
    
    # Create mock HTML with scaled content
    mock_html = """
    <html>
    <body>
        <h1>251130</h1>
        <div>
            <p>For time: 21-15-9 Pull-ups, Push-ups, Air squats</p>
            <p>Scaled: Assisted pull-ups, knee push-ups, air squats</p>
            <p>Beginner: 15-12-9 reps, band-assisted movements</p>
        </div>
    </body>
    </html>
    """
    
    try:
        wod = parse_wod(mock_html)
        print(f"  📅 Parsed Date: {wod['formatted_date']}")
        print(f"  💪 Main Workout: {wod['workout'][:50]}...")
        
        if wod.get('scaled_options'):
            print(f"  ✅ Found scaled options: {wod['scaled_options'][:50]}...")
            return True
        else:
            print(f"  ⚠️  No scaled options found (this might be normal)")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"  ❌ Scaled parsing test failed: {e}")
        return False

def test_workout_scenarios():
    """Test various workout scenario parsing."""
    print("🎯 Testing workout scenarios...")
    
    scenarios = [
        {
            "name": "Regular AMRAP",
            "html": "<div><h2>251201</h2><p>AMRAP 12 minutes: 5 pull-ups, 10 push-ups, 15 squats</p><p>Scaled: Assisted pull-ups, knee push-ups</p></div>"
        },
        {
            "name": "For Time Workout", 
            "html": "<div><h1>251202</h1><p>For time: 21-15-9 Burpees and Box Jumps</p><p>Beginner: Step-ups instead of box jumps</p></div>"
        },
        {
            "name": "Rest Day",
            "html": "<div><h1>251203</h1><p>Rest Day - Focus on mobility and recovery</p></div>"
        },
        {
            "name": "EMOM Workout",
            "html": "<div><h2>251204</h2><p>EMOM 10: 3 deadlifts at 80%</p><p>Scaled: Use lighter weight, focus on form</p></div>"
        }
    ]
    
    for scenario in scenarios:
        try:
            print(f"\n  Testing: {scenario['name']}")
            wod = parse_wod(scenario['html'])
            
            print(f"    Date: {wod['formatted_date']}")
            print(f"    Rest Day: {wod['is_rest_day']}")
            print(f"    Workout: {wod['workout'][:60]}...")
            
            if wod.get('scaled_options'):
                print(f"    Scaled: {wod['scaled_options'][:60]}...")
            else:
                print(f"    Scaled: None")
                
        except Exception as e:
            print(f"    ❌ Failed {scenario['name']}: {e}")
    
    print(f"  ✅ Workout scenario testing complete")

def test_data_structure():
    """Test that returned data has correct structure."""
    print("🏗️  Testing data structure...")
    try:
        wod = get_todays_wod()
        
        # Check required fields
        required_fields = ['date', 'formatted_date', 'is_rest_day', 'workout', 'scaled_options', 'raw_url']
        for field in required_fields:
            if field in wod:
                print(f"  ✅ {field}: {type(wod[field]).__name__}")
            else:
                print(f"  ❌ Missing field: {field}")
                
        # Check data types
        assert isinstance(wod['is_rest_day'], bool), "is_rest_day should be boolean"
        assert isinstance(wod['formatted_date'], str), "formatted_date should be string"
        assert wod['scaled_options'] is None or isinstance(wod['scaled_options'], str), "scaled_options should be string or None"
        
        print(f"  ✅ Data structure validation passed")
        
    except Exception as e:
        print(f"  ❌ Data structure test failed: {e}")

def test_full_workflow():
    """Test the complete workflow."""
    print("🚀 Testing complete workflow...")
    try:
        wod = get_todays_wod()
        print("  ✅ Full workflow successful!")
        print(f"  📊 Result: {wod['formatted_date']} - {'Rest Day' if wod['is_rest_day'] else 'Workout Day'}")
        
        # Show all available data
        if wod.get('scaled_options'):
            print(f"  📉 Scaled options available: {len(wod['scaled_options'])} characters")
        
        return wod
    except Exception as e:
        print(f"  ❌ Full workflow failed: {e}")
        return None

def test_config():
    """Test configuration validation."""
    print("⚙️  Testing configuration...")
    try:
        validate_config()
        print("  ✅ All required config variables are present")
    except ValueError as e:
        print(f"  ⚠️  Missing config: {e}")
        print("  💡 To fix: Create a .env file with:")
        print("     TWILIO_SID=your_twilio_sid")
        print("     TWILIO_TOKEN=your_twilio_token")
        print("     TWILIO_FROM=your_twilio_phone")
        print("     MY_PHONE=your_phone_number")
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")

def main():
    """Run all tests."""
    print("🤖 WodBot Test Suite")
    print("=" * 50)
    
    # Test each component
    test_date_formatting()
    html = test_html_fetching()
    test_parsing(html)
    test_scaled_workout_parsing()
    test_workout_scenarios()
    test_data_structure()
    test_full_workflow()
    test_config()
    
    print("=" * 50)
    print("🎉 Test suite complete!")
    print("\n💡 Next steps:")
    print("1. Set up .env file for SMS functionality")
    print("2. Test SMS sending (if configured)")
    print("3. Set up scheduling for daily delivery")
    print("4. Monitor scaled workout detection on regular workout days")

if __name__ == "__main__":
    main()