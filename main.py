"""
main.py — Orchestrates fetch -> analyze -> email

Usage:
  python main.py             # run once
  python main.py --schedule  # run every 5 minutes
"""

import sys
import os
from datetime import datetime
import schedule
import time

from fetcher import fetch_all_rates, format_rates_for_prompt
from agent import generate_summary
from emailer import send_email


def log(message):
    print(f"{datetime.now().strftime('%H:%M:%S')}  {message}", flush=True)


def run_pipeline():
    log("Starting agent")

    log("Fetching mortgage rates from FRED")
    try:
        rates = fetch_all_rates()
        rates_text = format_rates_for_prompt(rates)
    except Exception as e:
        log(f"Failed to fetch rates: {e}")
        return

    log("Connecting to Claude")
    try:
        data = generate_summary(rates_text)
        log(f"Summarized -- {data['signal']} {data['signal_label']} "
            f"(30yr: {data['rate_30yr']}%, 15yr: {data['rate_15yr']}%)")
    except Exception as e:
        log(f"Failed to generate summary: {e}")
        return

    log("Sending email")
    try:
        today = datetime.now().strftime("%B %d, %Y")
        subject = f"Mortgage Briefing {today} -- {data['signal']} {data['signal_label']}"
        send_email(subject=subject, data=data)
    except Exception as e:
        log(f"Failed to send email: {e}")
        return

    log("Done -- check your inbox")


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
        log("Scheduler mode -- running every 5 minutes (Ctrl+C to stop)")
        schedule.every(5).minutes.do(run_pipeline)
        run_pipeline()
        while True:
            schedule.run_pending()
            time.sleep(15)
    else:
        run_pipeline()


if __name__ == "__main__":
    main()