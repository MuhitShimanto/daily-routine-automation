import os
import json
import requests
from datetime import datetime, date
import pytz

# --- Constants and Configuration ---
# Timezone for Bangladesh
TIMEZONE = pytz.timezone("Asia/Dhaka") 
# Get today's date and day name based on the specified timezone
TODAY = datetime.now(TIMEZONE)
# Get just the date part for comparisons
TODAY_DATE = TODAY.date()
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
    
    todays_classes.sort(key=lambda x: datetime.strptime(x['time'].split('-')[0].strip(), "%I:%M %p"))
    class_messages = [f"• {c['course']} — {c['time']} at {c['room']} ({c['floor']})" for c in todays_classes]
    return "\n".join(class_messages)

def get_todays_learning(plan):
    """Get today's self-learning plan from a list of dated tasks."""
    if not plan:
        return "• No self-learning plan found."
        
    learning_tasks = [p['task'] for p in plan if p.get('date') == DATE_STR_MONTH_DAY]
    if not learning_tasks:
        return "• No specific learning tasks for today."
    task_messages = [f"• {task}" for task in learning_tasks]
    return "\n".join(task_messages)

def get_upcoming_deadlines(deadlines):
    """Gets all upcoming deadlines, sorted by date."""
    if not deadlines:
        return "• No deadlines found."

    upcoming = []
    for d in deadlines:
        try:
            # Convert deadline date string to a date object
            deadline_date = datetime.strptime(d['date'], '%Y-%m-%d').date()
            # Add to list if the deadline is today or in the future
            if deadline_date >= TODAY_DATE:
                upcoming.append(d)
        except (ValueError, KeyError):
            # Skip malformed entries
            continue
    
    if not upcoming:
        return "• No upcoming deadlines. You're all caught up!"

    # Sort the deadlines by date
    upcoming.sort(key=lambda x: x['date'])

    deadline_messages = []
    for d in upcoming:
        deadline_date = datetime.strptime(d['date'], '%Y-%m-%d').date()
        days_left = (deadline_date - TODAY_DATE).days
        
        # Format the due date string
        if days_left == 0:
            due_str = "Due Today!"
        elif days_left == 1:
            due_str = "Due Tomorrow!"
        else:
            # Format date as "Jul 26"
            formatted_date = deadline_date.strftime('%b %d')
            due_str = f"Due in {days_left} days ({formatted_date})"
            
        deadline_messages.append(f"• {d['task']} — {due_str}")

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

def send_telegram_message(bot_token, user_id, message):
    """Sends a message to a Telegram user with detailed error logging."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': user_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    print("\n--- Telegram Payload ---")
    print(json.dumps(payload, indent=2))
    print("------------------------\n")

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message. Status Code: {e.response.status_code}")
        print(f"Telegram API Response: {e.response.text}")

# --- Main Execution ---
if __name__ == "__main__":
    # --- Load Secrets from Environment Variables ---
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_USER_ID:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID must be set as environment variables.")
        exit(1)

    # --- Load Data ---
    class_routine = load_json_data("routines/class_routine.json")
    self_learning_plan = load_json_data("routines/self_learning.json")
    deadlines = load_json_data("routines/deadlines.json")
    special_events = load_json_data("routines/special_events.json")
    
    # --- Build Message Sections ---
    classes_section = get_todays_classes(class_routine)
    learning_section = get_todays_learning(self_learning_plan)
    deadlines_section = get_upcoming_deadlines(deadlines)
    events_section = get_todays_events(special_events)
    
    user_name = "Muhitul" 
    
    # --- Finalize and Send Message ---
    final_message = f"""
🗓️ *Good Morning {user_name}! Here's your plan for today ({FORMATTED_DATE}):*

🎓 *Classes*:
{classes_section}

📚 *Self-Learning*:
{learning_section}

📌 *Upcoming Deadlines*:
{deadlines_section}

🎯 *Special Events*:
{events_section}
"""
    
    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID, final_message)
