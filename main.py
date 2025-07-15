import os
import json
import requests
from datetime import datetime
import pytz

# --- Constants and Configuration ---
# Timezone for Bangladesh
TIMEZONE = pytz.timezone("Asia/Dhaka") 
# Get today's date and day name based on the specified timezone
TODAY = datetime.now(TIMEZONE)
DAY_NAME = TODAY.strftime('%A')
# Format for matching dates in deadlines.json and special_events.json (e.g., "2025-07-16")
DATE_STR_YMD = TODAY.strftime('%Y-%m-%d')
# Format for matching dates in self_learning.json (e.g., "July 16")
DATE_STR_MONTH_DAY = TODAY.strftime('%B %d')
# Formatted date for the message header (e.g., "Tuesday, July 15")
FORMATTED_DATE = TODAY.strftime('%A, %B %d')

# --- Helper Functions ---

def load_json_data(file_path):
    """Safely loads data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return [] # Return an empty list on error for safer processing

def get_todays_classes(routine):
    """Get today's class schedule from a list of classes."""
    if not routine:
        return "• No classes found in routine file."
    
    todays_classes = [c for c in routine if c.get('day', '').lower() == DAY_NAME.lower()]

    if not todays_classes:
        return "• No classes today. Enjoy the free time!"
    
    # Sort classes by time to ensure they are in chronological order
    todays_classes.sort(key=lambda x: datetime.strptime(x['time'].split('-')[0].strip(), "%I:%M %p"))

    class_messages = [f"• {c['course']} — {c['time']} at {c['room']} ({c['floor']})" for c in todays_classes]
    return "\n".join(class_messages)

def get_todays_learning(plan):
    """Get today's self-learning plan from a list of dated tasks."""
    if not plan:
        return "• No self-learning plan found."
        
    # Find tasks that match today's date (e.g., "July 16")
    learning_tasks = [p['task'] for p in plan if p.get('date') == DATE_STR_MONTH_DAY]

    if not learning_tasks:
        return "• No specific learning tasks for today."

    task_messages = [f"• {task}" for task in learning_tasks]
    return "\n".join(task_messages)

def get_todays_deadlines(deadlines):
    """Get deadlines that are due today from a list."""
    if not deadlines:
        return "• No deadlines found."

    due_today = [d for d in deadlines if d.get('date') == DATE_STR_YMD]
    
    if not due_today:
        return "• No deadlines today. Keep up the great work!"
        
    deadline_messages = [f"• {d['task']} — Due Today!" for d in due_today]
    return "\n".join(deadline_messages)

def get_todays_events(events):
    """Get special events for today from a list."""
    if not events:
        return "• No special events scheduled for today."

    today_events = [e for e in events if e.get('date') == DATE_STR_YMD]

    if not today_events:
        return "• No special events scheduled for today."

    event_messages = [f"• {e['event']} — {e['time']} @ {e['location']}" for e in today_events]
    return "\n".join(event_messages)

def get_gemini_advice(api_key, full_schedule):
    """Gets dynamic advice from the Gemini API."""
    if not api_key:
        return "To get AI advice, set your GEMINI_API_KEY secret in GitHub Actions."

    prompt = (
        "You are a friendly and motivational student advisor. "
        "Based on the following schedule for a student in Bangladesh, provide one or two short, encouraging sentences of advice. "
        "Focus on prioritizing tasks, managing time, or staying motivated. Add a positive emoji at the end.\n\n"
        f"Today's Schedule:\n{full_schedule}"
    )
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        
        if (result.get('candidates') and 
            result['candidates'][0].get('content') and 
            result['candidates'][0]['content'].get('parts')):
            advice = result['candidates'][0]['content']['parts'][0]['text']
            return advice.strip()
        else:
            print("Gemini API response format is unexpected:", result)
            return "Couldn't generate advice today, but keep pushing forward! You can do it. ✨"

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return "Could not fetch AI advice due to a network error. But remember to stay focused! 👍"
    except Exception as e:
        print(f"An unexpected error occurred with Gemini API: {e}")
        return "An unexpected error occurred while getting advice. Have a great day! 😊"

def get_productivity_tip():
    """Returns a random productivity tip."""
    tips = [
        "Try the Pomodoro Technique: 25 minutes of focused work followed by a 5-minute break.",
        "Use the 2-Minute Rule: If a task takes less than two minutes, do it now.",
        "Eat the Frog: Tackle your most challenging task first thing in the morning.",
        "Time blocking can help you focus. Assign specific time slots for each task on your calendar.",
        "Minimize distractions. Put your phone on silent and close unnecessary tabs while you study.",
        "Prepare for tomorrow tonight. A little planning before bed can make your morning much smoother."
    ]
    import random
    return random.choice(tips)

def send_telegram_message(bot_token, user_id, message):
    """Sends a message to a Telegram user."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': user_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

# --- Main Execution ---

if __name__ == "__main__":
    # --- Load Secrets from Environment Variables ---
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_USER_ID:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID must be set as environment variables.")
        exit(1)

    # --- Load Data from your JSON Files ---
    class_routine = load_json_data("routines/class_routine.json")
    self_learning_plan = load_json_data("routines/self_learning.json")
    deadlines = load_json_data("routines/deadlines.json")
    special_events = load_json_data("routines/special_events.json")
    
    # --- Build Message Sections ---
    classes_section = get_todays_classes(class_routine)
    learning_section = get_todays_learning(self_learning_plan)
    deadlines_section = get_todays_deadlines(deadlines)
    events_section = get_todays_events(special_events)
    
    # --- Construct the Full Message ---
    user_name = "Muhitul" 
    
    schedule_summary = f"""
🎓 *Classes*:
{classes_section}

📚 *Self-Learning*:
{learning_section}

📌 *Deadlines*:
{deadlines_section}

🎯 *Special Events*:
{events_section}
"""
    
    # --- Get Dynamic Advice and Tip ---
    ai_advice = get_gemini_advice(GEMINI_API_KEY, schedule_summary)
    productivity_tip = get_productivity_tip()

    # --- Finalize and Send Message ---
    final_message = f"""
🗓️ *Good Morning {user_name}! Here's your plan for today ({FORMATTED_DATE}):*

{schedule_summary}
💡 *Gemini says*:
"{ai_advice}"

🌟 *Productivity Tip*:
{productivity_tip}
"""

    print("--- Sending Message ---")
    print(final_message)
    print("-----------------------")
    
    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID, final_message)
