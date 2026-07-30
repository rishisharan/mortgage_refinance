"""
main.py — Orchestrates fetch -> analyze -> email

Usage:
  python main.py             # run once
  python main.py --schedule  # run daily at 8am
"""

import sys
import os
from datetime import datetime
import schedule
import time

from fetcher import fetch_all_rates, format_rates_for_prompt
from agent import generate_summary
from emailer import send_email


def run_pipeline():
    print(f"\n{'='*50}")
    print(f"  Mortgage Rate Tracker")
    print(f"  {datetime.now().strftime('%A, %B %d %Y at %I:%M %p')}")
    print(f"{'='*50}\n")

    # Step 1: Fetch rates
    print("Step 1: Fetching mortgage rates from FRED...")
    try:
        rates = fetch_all_rates()
        rates_text = format_rates_for_prompt(rates)
        print(f"\n  Raw data:\n{rates_text}\n")
    except Exception as e:
        print(f"Failed to fetch rates: {e}")
        return

    # Step 2: Generate structured summary
    print("Step 2: Generating AI summary...")
    try:
        data = generate_summary(rates_text)
        print(f"  Signal: {data['signal']} -- {data['signal_label']}")
        print(f"  30yr: {data['rate_30yr']}%  |  15yr: {data['rate_15yr']}%\n")
    except Exception as e:
        print(f"Failed to generate summary: {e}")
        return

    # Step 3: Send visual email
    print("Step 3: Sending email...")
    try:
        today = datetime.now().strftime("%B %d, %Y")
        subject = f"Mortgage Briefing {today} -- {data['signal']} {data['signal_label']}"
        send_email(subject=subject, data=data)
    except Exception as e:
        print(f"Failed to send email: {e}")
        return

    print(f"\nDone! Check your inbox.\n")


def check_env_vars():
    required = ["ANTHROPIC_API_KEY", "FRED_API_KEY", "MAILERSEND_API_KEY",
                "SENDER_EMAIL", "RECIPIENT_EMAIL"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print("Missing environment variables:")
        for v in missing:
            print(f"   $env:{v} = 'your-value-here'")
        sys.exit(1)


def main():
    check_env_vars()

    if "--schedule" in sys.argv:
        print("Scheduler mode -- running daily at 8:00 AM")
        print("Leave this window open. Ctrl+C to stop.\n")
        schedule.every().day.at("08:00").do(run_pipeline)
        run_pipeline()
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_pipeline()


if __name__ == "__main__":
    main()