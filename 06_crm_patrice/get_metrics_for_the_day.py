from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from telegram_services.telegram import send_telegram_text_message
from get_spreadsheet_calendar_daily_metrics import DailyMetricsReader
from database.logging_service import SupabaseLoggingService

load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

daily_metrics_reader = DailyMetricsReader()
logging_service = SupabaseLoggingService()

def format_time_ago(last_interaction):
    """Format the time difference in a human-readable way"""
    if not last_interaction:
        return "Never"
    
    # Parse the ISO string to datetime
    if isinstance(last_interaction, str):
        last_interaction = datetime.fromisoformat(last_interaction.replace('Z', '+00:00'))
    
    now = datetime.now(last_interaction.tzinfo) if last_interaction.tzinfo else datetime.now()
    time_diff = now - last_interaction
    
    if time_diff.days > 0:
        return f"{time_diff.days} day{'s' if time_diff.days != 1 else ''} ago"
    elif time_diff.seconds >= 3600:
        hours = time_diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif time_diff.seconds >= 60:
        minutes = time_diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def get_urgency_status(last_interaction):
    """Determine urgency status based on last interaction"""
    if not last_interaction:
        return "URGENT", "🔴"
    
    if isinstance(last_interaction, str):
        last_interaction = datetime.fromisoformat(last_interaction.replace('Z', '+00:00'))
    
    now = datetime.now(last_interaction.tzinfo) if last_interaction.tzinfo else datetime.now()
    days_since = (now - last_interaction).days
    
    if days_since > 10:
        return "URGENT", "🔴"
    elif days_since > 3:
        return "NEEDS ATTENTION", "🟡"
    else:
        return "OK", "🟢"

def generate_metrics_text(clients):
    """Generate metrics text for Telegram"""
    urgent_count = 0
    needs_attention_count = 0
    ok_count = 0
    active_count = 0
    inactive_count = 0
    
    for client in clients:
        urgency, _ = get_urgency_status(client.get('last_interaction'))
        if urgency == "URGENT":
            urgent_count += 1
        elif urgency == "NEEDS ATTENTION":
            needs_attention_count += 1
        else:
            ok_count += 1
        
        if client.get('status') == 'active':
            active_count += 1
        else:
            inactive_count += 1
    
    metrics_text = f"""📊 SUMMARY METRICS
🔴 URGENT (>10 days): {urgent_count} clients
🟡 NEEDS ATTENTION (3-10 days): {needs_attention_count} clients
🟢 OK (<3 days): {ok_count} clients

✅ Active clients: {active_count}
❌ Inactive clients: {inactive_count}
📈 Total clients: {len(clients)}"""
    
    return metrics_text

def generate_client_section_text(title, clients, urgency_filter=None):
    """Generate client section text for Telegram"""
    filtered_clients = []
    for client in clients:
        urgency, _ = get_urgency_status(client.get('last_interaction'))
        if urgency_filter is None or urgency == urgency_filter:
            filtered_clients.append(client)
    
    if not filtered_clients:
        return ""
    
    section_text = f"\n�� {title}\n{'-' * 40}\n"
    
    for client in filtered_clients:
        urgency, emoji = get_urgency_status(client.get('last_interaction'))
        time_ago = format_time_ago(client.get('last_interaction'))
        status_emoji = "✅" if client.get('status') == 'active' else "❌"
        
        section_text += f"{emoji} {client['name']} | {client['email']} | {time_ago} | {status_emoji} {client.get('status', 'unknown')}\n"
    
    return section_text

def generate_telegram_report(clients, daily_metrics=None):
    """Generate the complete Telegram report"""
    # Get current date once
    current_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    header = f"""🤖 DAILY REPORT - {current_date}
{'='*40}"""

    # Add daily metrics if available
    daily_section = ""
    if daily_metrics and daily_metrics.get('success'):
        data = daily_metrics['data']
        cells_below = data['cells_below']
        
        # Get tasks (only non-empty ones)
        tasks = []
        for cell_info in cells_below:
            value = cell_info['value'].strip() if cell_info['value'] else ''
            if value:
                if cell_info['has_link']:
                    tasks.append(f"• 🔗 {value}")
                else:
                    tasks.append(f"• {value}")
        
        if tasks:
            daily_section = f"""
📅 TODAY'S TASKS:
{chr(10).join(tasks)}"""
        else:
            daily_section = """
📅 TODAY'S TASKS:
   No tasks scheduled for today"""
    
    metrics = generate_metrics_text(clients)
    
    urgent_section = generate_client_section_text("URGENT CLIENTS (>10 days)", clients, "URGENT")
    needs_attention_section = generate_client_section_text("NEEDS ATTENTION (3-10 days)", clients, "NEEDS ATTENTION")
    ok_section = generate_client_section_text("RECENTLY CONTACTED (<3 days)", clients, "OK")
    
    footer = f"""
{'='*40}
Report complete. Prioritize 🔴 URGENT clients for immediate follow-up."""

    # Combine all sections
    full_report = f"{header}{daily_section}\n\n{metrics}"
    
    if urgent_section:
        full_report += urgent_section
    
    if needs_attention_section:
        full_report += needs_attention_section
    
    if ok_section:
        full_report += ok_section
    
    full_report += footer
    
    return full_report

def print_header():
    """Print the report header"""
    print("=" * 80)
    print("                    DAILY REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print()

def print_metrics(clients):
    """Print metrics section"""
    urgent_count = 0
    needs_attention_count = 0
    ok_count = 0
    active_count = 0
    inactive_count = 0
    
    for client in clients:
        urgency, _ = get_urgency_status(client.get('last_interaction'))
        if urgency == "URGENT":
            urgent_count += 1
        elif urgency == "NEEDS ATTENTION":
            needs_attention_count += 1
        else:
            ok_count += 1
        
        if client.get('status') == 'active':
            active_count += 1
        else:
            inactive_count += 1
    
    print("📊 SUMMARY METRICS")
    print("-" * 40)
    print(f"🔴 URGENT (>10 days):     {urgent_count:2d} clients")
    print(f"🟡 NEEDS ATTENTION (3-10 days): {needs_attention_count:2d} clients")
    print(f"🟢 OK (<3 days):         {ok_count:2d} clients")
    print()
    print(f"✅ Active clients:        {active_count:2d}")
    print(f"❌ Inactive clients:      {inactive_count:2d}")
    print(f"📈 Total clients:         {len(clients):2d}")
    print()
    print("=" * 80)
    print()

def print_client_section(title, clients, urgency_filter=None):
    """Print a section of clients with the given urgency"""
    filtered_clients = []
    for client in clients:
        urgency, _ = get_urgency_status(client.get('last_interaction'))
        if urgency_filter is None or urgency == urgency_filter:
            filtered_clients.append(client)
    
    if not filtered_clients:
        return
    
    print(f"📋 {title}")
    print("-" * 80)
    
    for client in filtered_clients:
        urgency, emoji = get_urgency_status(client.get('last_interaction'))
        time_ago = format_time_ago(client.get('last_interaction'))
        status_emoji = "✅" if client.get('status') == 'active' else "❌"
        
        print(f"{emoji} {client['name']:<25} | {client['email']:<30} | {time_ago:<15} | {status_emoji} {client.get('status', 'unknown')}")
    
    print()

def print_daily_metrics_section(metrics_data):
    """Print daily metrics section for console"""
    if not metrics_data or not metrics_data.get('success'):
        print("❌ No daily metrics available")
        return
    
    data = metrics_data['data']
    cells_below = data['cells_below']
    
    print("📅 TODAY'S TASKS:")
    print("-" * 40)
    
    # Get tasks (only non-empty ones)
    task_count = 0
    for cell_info in cells_below:
        value = cell_info['value'].strip() if cell_info['value'] else ''
        if value:
            task_count += 1
            if cell_info['has_link']:
                print(f"{task_count}. 🔗 {value}")
                print(f"   Link: {cell_info['hyperlink']}")
            else:
                print(f"{task_count}. {value}")
    
    if task_count == 0:
        print("   No tasks scheduled for today")
    
    print()

def get_daily_metrics():
    """Get daily metrics from the spreadsheet"""
    try:
        return daily_metrics_reader.get_daily_metrics()
    except Exception as e:
        error_msg = f"Error getting daily metrics: {e}"
        print(f"❌ {error_msg}")
        logging_service.log_error(error_msg, "daily_metrics_retrieval")
        return {'success': False, 'error': str(e), 'data': None}

# Main execution
try:
    print("🚀 Starting daily metrics report generation...")
    
    # Get all clients ordered by last interaction (most recent first)
    response = supabase.table('clients').select('*').order('last_interaction', desc=True).execute()
    clients = response.data
    
    print(f"📊 Retrieved {len(clients)} clients from database")
    
    # Get daily metrics
    daily_metrics = get_daily_metrics()
    
    if not daily_metrics.get('success'):
        print("⚠️ Failed to retrieve daily metrics")
        logging_service.log_error("Failed to retrieve daily metrics", "daily_metrics_retrieval")
    
    # Generate and send the unified Telegram report
    telegram_report = generate_telegram_report(clients, daily_metrics)
    send_telegram_text_message(telegram_report)
    
    print("✅ Successfully sent Telegram report")
    logging_service.log_activity(
        action="telegram_report_sent",
        description="Successfully sent daily report via Telegram"
    )
    
    # Print the unified report to console as well
    print_header()
    print_daily_metrics_section(daily_metrics)
    print_metrics(clients)
    
    print_client_section("URGENT CLIENTS (>10 days since last interaction)", clients, "URGENT")
    print_client_section("CLIENTS NEEDING ATTENTION (3-10 days since last interaction)", clients, "NEEDS ATTENTION")
    print_client_section("RECENTLY CONTACTED CLIENTS (<3 days since last interaction)", clients, "OK")
    
    print("=" * 80)
    print("Report complete. Prioritize clients marked as 🔴 URGENT for immediate follow-up.")
    print("=" * 80)
    
except Exception as e:
    error_msg = f"Error in daily metrics report generation: {e}"
    print(f"❌ {error_msg}")
    logging_service.log_error(error_msg, "daily_report_generation")