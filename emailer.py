"""
emailer.py — Sends the mortgage rate summary via MailerSend API

Setup:
  1. Go to app.mailersend.com -> API Tokens -> Create token
  2. Verify your sending domain in MailerSend
  3. Set environment variables:
     $env:MAILERSEND_API_KEY  = "mlsn.your-key-here"
     $env:SENDER_EMAIL        = "you@yourdomain.com"  <- must be verified in MailerSend
     $env:SENDER_NAME         = "Mortgage Tracker"    <- display name (optional)
     $env:RECIPIENT_EMAIL     = "you@gmail.com"       <- where you want it delivered

    #TODO:  $env:MAILERSEND_API_KEY  = "" 
     $env:SENDER_EMAIL        = "chapterconnect009@gmail.com"
     $env:SENDER_NAME         = "Mortgage Tracker"
     $env:RECIPIENT_EMAIL     = "prishisharan28@gmail.com"
"""

"""
emailer.py — Builds a visual HTML email and sends via MailerSend

Setup:
  $env:MAILERSEND_API_KEY = "mlsn.your-key-here"
  $env:SENDER_EMAIL       = "noreply@test-q3enl6kemy842vwr.mlsender.net"
  $env:SENDER_NAME        = "Mortgage Tracker"
  $env:RECIPIENT_EMAIL    = "prishisharan28@gmail.com"
"""

import os
import json
import requests
from datetime import datetime

MAILERSEND_API_URL = "https://api.mailersend.com/v1/email"


def build_html(d: dict, date_str: str) -> str:
    """Builds the visual HTML email from structured data dict."""

    # Signal colors
    signal_colors = {
        "GREEN":  {"bg": "#E1F5EE", "text": "#0F6E56", "border": "#1D9E75", "dot": "#1D9E75"},
        "YELLOW": {"bg": "#FAEEDA", "text": "#854F0B", "border": "#EF9F27", "dot": "#EF9F27"},
        "RED":    {"bg": "#FCEBEB", "text": "#A32D2D", "border": "#E24B4A", "dot": "#E24B4A"},
    }
    sc = signal_colors.get(d["signal"], signal_colors["GREEN"])

    # Rate change arrows
    def change_str(val):
        if val > 0:   return f'<span style="color:#E24B4A">▲ +{val:.2f}%</span>'
        elif val < 0: return f'<span style="color:#1D9E75">▼ {val:.2f}%</span>'
        else:         return '<span style="color:#888">→ unchanged</span>'

    # CSS bar chart — max bar = 100%, others scaled
    max_interest = max(d["total_interest_arm"], d["total_interest_15yr"], d["total_interest_30yr"])
    def bar_pct(val): return round(val / max_interest * 100)

    bar_arm  = bar_pct(d["total_interest_arm"])
    bar_15yr = bar_pct(d["total_interest_15yr"])
    bar_30yr = bar_pct(d["total_interest_30yr"])

    def fmt(n): return f"${n:,.0f}"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mortgage Rate Briefing</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f0;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f0;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e5e5e0;">

  <!-- Header -->
  <tr><td style="background:#1a3a5c;padding:24px 32px;">
    <p style="margin:0;font-size:11px;color:#7aa3c8;letter-spacing:1px;text-transform:uppercase;">Daily Briefing &bull; {date_str}</p>
    <h1 style="margin:6px 0 0;font-size:22px;color:#ffffff;font-weight:normal;">Mortgage Rate Report</h1>
  </td></tr>

  <!-- Signal banner -->
  <tr><td style="padding:0 32px;">
    <div style="background:{sc['bg']};border-left:4px solid {sc['border']};border-radius:0 8px 8px 0;padding:14px 18px;margin:24px 0 0;">
      <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{sc['dot']};margin-right:8px;vertical-align:middle;"></span>
      <strong style="color:{sc['text']};font-size:14px;">REFI SIGNAL: {d['signal']} &mdash; {d['signal_label']}</strong>
      <p style="margin:6px 0 0;font-size:13px;color:{sc['text']};">{d['signal_reason']}</p>
    </div>
  </td></tr>

  <!-- Headline -->
  <tr><td style="padding:20px 32px 0;">
    <p style="margin:0;font-size:16px;color:#1a3a5c;line-height:1.6;font-style:italic;">"{d['headline']}"</p>
  </td></tr>

  <!-- Today's rates vs your rate -->
  <tr><td style="padding:20px 32px 0;">
    <p style="margin:0 0 12px;font-size:11px;color:#888;letter-spacing:1px;text-transform:uppercase;">Today's Rates vs Your Rate</p>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td width="31%" style="background:#f8f8f5;border-radius:8px;padding:14px 16px;text-align:center;">
          <p style="margin:0;font-size:11px;color:#888;">Your ARM</p>
          <p style="margin:4px 0 0;font-size:24px;font-weight:bold;color:#1D9E75;">3.875%</p>
          <p style="margin:4px 0 0;font-size:11px;color:#1D9E75;">locked 1 more year</p>
        </td>
        <td width="4%"></td>
        <td width="31%" style="background:#f8f8f5;border-radius:8px;padding:14px 16px;text-align:center;">
          <p style="margin:0;font-size:11px;color:#888;">30yr Fixed</p>
          <p style="margin:4px 0 0;font-size:24px;font-weight:bold;color:#1a3a5c;">{d['rate_30yr']:.2f}%</p>
          <p style="margin:4px 0 0;font-size:11px;color:#888;">{change_str(d['rate_change_30yr'])}</p>
        </td>
        <td width="4%"></td>
        <td width="31%" style="background:#f8f8f5;border-radius:8px;padding:14px 16px;text-align:center;">
          <p style="margin:0;font-size:11px;color:#888;">15yr Fixed</p>
          <p style="margin:4px 0 0;font-size:24px;font-weight:bold;color:#1a3a5c;">{d['rate_15yr']:.2f}%</p>
          <p style="margin:4px 0 0;font-size:11px;color:#888;">{change_str(d['rate_change_15yr'])}</p>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- Analysis -->
  <tr><td style="padding:20px 32px 0;">
    <p style="margin:0;font-size:14px;color:#333;line-height:1.8;">{d['body']}</p>
  </td></tr>

  <!-- Your numbers -->
  <tr><td style="padding:20px 32px 0;">
    <p style="margin:0 0 12px;font-size:11px;color:#888;letter-spacing:1px;text-transform:uppercase;">Your Current Snapshot</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e5e0;border-radius:8px;overflow:hidden;">
      <tr style="background:#f8f8f5;">
        <td style="padding:10px 16px;font-size:13px;color:#555;border-bottom:1px solid #e5e5e0;">Balance</td>
        <td style="padding:10px 16px;font-size:13px;font-weight:bold;color:#1a3a5c;text-align:right;border-bottom:1px solid #e5e5e0;">$289,830</td>
      </tr>
      <tr>
        <td style="padding:10px 16px;font-size:13px;color:#555;border-bottom:1px solid #e5e5e0;">Monthly P&amp;I</td>
        <td style="padding:10px 16px;font-size:13px;font-weight:bold;color:#1a3a5c;text-align:right;border-bottom:1px solid #e5e5e0;">$1,325 ($520 principal + $805 interest)</td>
      </tr>
      <tr style="background:#f8f8f5;">
        <td style="padding:10px 16px;font-size:13px;color:#555;border-bottom:1px solid #e5e5e0;">Total PITI</td>
        <td style="padding:10px 16px;font-size:13px;font-weight:bold;color:#1a3a5c;text-align:right;border-bottom:1px solid #e5e5e0;">$2,036/mo</td>
      </tr>
      <tr>
        <td style="padding:10px 16px;font-size:13px;color:#555;border-bottom:1px solid #e5e5e0;">ARM adjusts</td>
        <td style="padding:10px 16px;font-size:13px;font-weight:bold;color:#E24B4A;text-align:right;border-bottom:1px solid #e5e5e0;">~April 2027 &rarr; max 5.875%</td>
      </tr>
      <tr style="background:#f8f8f5;">
        <td style="padding:10px 16px;font-size:13px;color:#555;">After adjustment</td>
        <td style="padding:10px 16px;font-size:13px;font-weight:bold;color:#E24B4A;text-align:right;">PITI jumps to ~$2,501/mo (+$465)</td>
      </tr>
    </table>
  </td></tr>

  <!-- Bar chart: total interest -->
  <tr><td style="padding:20px 32px 0;">
    <p style="margin:0 0 16px;font-size:11px;color:#888;letter-spacing:1px;text-transform:uppercase;">Total Interest Paid — All Scenarios</p>

    <!-- ARM bar -->
    <p style="margin:0 0 4px;font-size:12px;color:#555;">Keep ARM (adjusts to ~5.875%)</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
      <tr>
        <td width="{bar_arm}%" style="background:#B5D4F4;height:28px;border-radius:4px;"></td>
        <td style="padding-left:10px;font-size:13px;font-weight:bold;color:#1a3a5c;white-space:nowrap;">{fmt(d['total_interest_arm'])}</td>
      </tr>
    </table>

    <!-- 15yr bar -->
    <p style="margin:0 0 4px;font-size:12px;color:#555;">Refi to 15yr @ {d['rate_15yr']:.2f}% <span style="color:#1D9E75;font-size:11px;">saves {fmt(d['interest_saved_15yr'])}</span></p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
      <tr>
        <td width="{bar_15yr}%" style="background:#5DCAA5;height:28px;border-radius:4px;"></td>
        <td style="padding-left:10px;font-size:13px;font-weight:bold;color:#1D9E75;white-space:nowrap;">{fmt(d['total_interest_15yr'])}</td>
      </tr>
    </table>

    <!-- 30yr bar -->
    <p style="margin:0 0 4px;font-size:12px;color:#555;">Refi to 30yr @ {d['rate_30yr']:.2f}% <span style="color:#E24B4A;font-size:11px;">avoid — resets clock</span></p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:4px;">
      <tr>
        <td width="{bar_30yr}%" style="background:#F09595;height:28px;border-radius:4px;"></td>
        <td style="padding-left:10px;font-size:13px;font-weight:bold;color:#E24B4A;white-space:nowrap;">{fmt(d['total_interest_30yr'])}</td>
      </tr>
    </table>
  </td></tr>

  <!-- Action -->
  <tr><td style="padding:20px 32px;">
    <div style="background:#1a3a5c;border-radius:8px;padding:16px 20px;">
      <p style="margin:0;font-size:11px;color:#7aa3c8;letter-spacing:1px;text-transform:uppercase;">Today's Action</p>
      <p style="margin:8px 0 0;font-size:14px;color:#ffffff;line-height:1.6;">{d['action']}</p>
    </div>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#f8f8f5;padding:16px 32px;border-top:1px solid #e5e5e0;">
    <p style="margin:0;font-size:11px;color:#aaa;line-height:1.6;">
      Data from Federal Reserve (FRED) &bull; Rates as of {date_str}<br>
      This is not financial advice. Consult a licensed mortgage professional before making decisions.
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""
    return html


def send_email(subject: str, data: dict) -> None:
    """
    Builds the HTML email from structured data and sends via MailerSend.
    """
    api_key     = os.environ.get("MAILERSEND_API_KEY")
    sender      = os.environ.get("SENDER_EMAIL")
    sender_name = os.environ.get("SENDER_NAME", "Mortgage Tracker")
    recipient   = os.environ.get("RECIPIENT_EMAIL")

    missing = []
    if not api_key:   missing.append("MAILERSEND_API_KEY")
    if not sender:    missing.append("SENDER_EMAIL")
    if not recipient: missing.append("RECIPIENT_EMAIL")
    if missing:
        raise ValueError(f"Missing env vars: {', '.join(missing)}")

    date_str = datetime.now().strftime("%B %d, %Y")
    html = build_html(data, date_str)

    # Plain text fallback
    plain = (
        f"Mortgage Rate Briefing — {date_str}\n\n"
        f"30yr: {data['rate_30yr']:.2f}%  |  15yr: {data['rate_15yr']:.2f}%  |  Your ARM: 3.875%\n\n"
        f"{data['headline']}\n\n"
        f"{data['body']}\n\n"
        f"Today's action: {data['action']}\n\n"
        f"REFI SIGNAL: {data['signal']} — {data['signal_label']} — {data['signal_reason']}"
    )

    payload = {
        "from":    {"email": sender, "name": sender_name},
        "to":      [{"email": recipient}],
        "subject": subject,
        "text":    plain,
        "html":    html
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json"
    }

    print(f"  Sending email to {recipient} via MailerSend...")
    response = requests.post(MAILERSEND_API_URL, headers=headers, data=json.dumps(payload), timeout=15)

    if response.status_code == 202:
        print("  Email sent!")
    else:
        raise RuntimeError(f"MailerSend error {response.status_code}: {response.text}")