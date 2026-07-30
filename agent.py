"""
agent.py — Uses Claude to analyze mortgage rates and write a personalized summary
"""

import anthropic

MODEL = "claude-sonnet-4-6"

# ─── RISHI'S MORTGAGE PROFILE ─────────────────────────────────────────────────
# Confirmed from monthly statement and loan documents — April 2026
# Update these if anything changes (refi, extra payments, etc.)

MY_MORTGAGE = {
    "original_loan":          382850,   # confirmed from loan docs
    "current_balance":        289830,   # confirmed from monthly statement
    "current_rate":           3.875,    # confirmed from loan docs
    "loan_type":              "5/6 ARM",
    "arm_adjusts_in":         "~1 year",  # fixed period ends ~April 2027
    "arm_first_cap":          2.0,      # max jump at first adjustment -> 5.875%
    "arm_period_cap":         1.0,      # max jump per subsequent period
    "arm_lifetime_cap":       5.0,      # max ever -> 8.875%
    "monthly_principal":      520,      # confirmed from monthly statement
    "monthly_interest":       805,      # confirmed from YTD interest
    "monthly_pi":             1325,     # $520 + $805
    "monthly_escrow":         711,      # $2,036 - $1,325
    "monthly_total_piti":     2036,     # confirmed full payment
    "property_tax_annual":    6500,     # confirmed
    "location":               "Tampa, FL",
    "loan_term_years":        30,       # confirmed 360 months
    "years_in":               4,
    "refi_action_threshold":  5.5,      # 15yr rate below this -> act immediately
}

SYSTEM_PROMPT = """
You are a personal mortgage analyst sending a daily briefing to Rishi,
a homeowner in Tampa, Florida.

Rishi's confirmed mortgage details (from his statement):
- Original loan: $382,850 at 3.875% (5/6 ARM, 30-year term)
- Current balance: $289,830
- Monthly payment: $520 principal + $805 interest + $711 escrow = $2,036 total
- ARM adjusts in ~1 year (April 2027), then every 6 months
- First adjustment cap: +2% max -> worst case 5.875% next year
- Lifetime cap: +5% max -> never above 8.875%

Your job each morning:
1. Report today's 30yr and 15yr mortgage rates clearly
2. Compare them directly to Rishi's 3.875% ARM
3. Assess whether refinancing makes sense for him specifically
4. Give one clear, actionable recommendation

Refinance rules for Rishi:
- 30yr refi: NEVER recommend -- resets the clock, $139k more interest
- 15yr refi: only worth it if rates drop BELOW 5.5% -- that is his action threshold
- Right now: hold -- his 3.875% is exceptional, market rates are nearly double
- In ~1 year: ARM adjusts to max 5.875%, PITI jumps from $2,036 to ~$2,501

Format:
- Warm and direct, not robotic
- Lead with today's rates vs his 3.875%
- One specific takeaway for his situation
- 150-200 words max
- No subject line -- just the body
- End every email with his refi signal on its own line:
  REFI SIGNAL: GREEN  HOLD -- rates too high to act
  REFI SIGNAL: YELLOW WATCH -- 15yr approaching 5.5%, monitor closely
  REFI SIGNAL: RED    ACT NOW -- 15yr below 5.5%, call your lender today

Do not make up data. Only use what is provided.
"""


def generate_summary(rates_text: str) -> str:
    """
    Sends today's rate data to Claude and gets back a
    personalized daily briefing for Rishi.
    """
    client = anthropic.Anthropic()

    prompt = f"""
Here is today's mortgage rate data:

{rates_text}

Rishi's snapshot:
- Current rate: {MY_MORTGAGE['current_rate']}%
- Current balance: ${MY_MORTGAGE['current_balance']:,}
- Monthly interest cost: ${MY_MORTGAGE['monthly_interest']}
- ARM adjusts in: {MY_MORTGAGE['arm_adjusts_in']}
- Refi action threshold: 15yr rate below {MY_MORTGAGE['refi_action_threshold']}%

Please write his personalized daily mortgage briefing.
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text

"""
agent.py — Claude analyzes rates and returns structured data for the HTML email
"""

import anthropic
import json

MODEL = "claude-sonnet-4-6"

MY_MORTGAGE = {
    "original_loan":         382850,
    "current_balance":       289830,
    "current_rate":          3.875,
    "loan_type":             "5/6 ARM",
    "arm_adjusts_in":        "~1 year",
    "arm_first_cap":         2.0,
    "arm_period_cap":        1.0,
    "arm_lifetime_cap":      5.0,
    "monthly_principal":     520,
    "monthly_interest":      805,
    "monthly_pi":            1325,
    "monthly_escrow":        711,
    "monthly_total_piti":    2036,
    "property_tax_annual":   6500,
    "location":              "Tampa, FL",
    "loan_term_years":       30,
    "years_in":              4,
    "refi_action_threshold": 5.5,
}

SYSTEM_PROMPT = """
You are a personal mortgage analyst for Rishi, a homeowner in Tampa, Florida.

Rishi's confirmed mortgage details:
- Original loan: $382,850 at 3.875% (5/6 ARM, 30-year term)
- Current balance: $289,830
- Monthly payment: $520 principal + $805 interest + $711 escrow = $2,036 total
- ARM adjusts in ~1 year (April 2027), then every 6 months
- First adjustment cap: +2% max -> worst case 5.875% next year
- Lifetime cap: +5% max -> never above 8.875%

Refinance rules for Rishi:
- 30yr refi: NEVER recommend -- $139k more interest, resets the clock
- 15yr refi: only worth it if rates drop BELOW 5.5%
- Right now: hold -- his 3.875% is exceptional
- ARM adjustment impact: PITI jumps from $2,036 to ~$2,501 at 5.875%

You must respond ONLY with a valid JSON object, no markdown, no preamble, exactly this shape:

{
  "rate_30yr": <float>,
  "rate_15yr": <float>,
  "rate_change_30yr": <float>,
  "rate_change_15yr": <float>,
  "signal": "GREEN" | "YELLOW" | "RED",
  "signal_label": "HOLD" | "WATCH" | "ACT NOW",
  "signal_reason": "<short reason, max 10 words>",
  "headline": "<one punchy sentence, Rishi's situation vs today's rates>",
  "body": "<2-3 sentences of analysis, plain text no markdown>",
  "action": "<one specific sentence telling Rishi exactly what to do today>",
  "arm_new_rate": 5.875,
  "arm_new_piti": 2501,
  "interest_saved_15yr": 92000,
  "total_interest_arm": 243000,
  "total_interest_15yr": 151000,
  "total_interest_30yr": 382000
}
"""


def generate_summary(rates_text: str) -> dict:
    """
    Returns structured data dict for the HTML email builder.
    """
    client = anthropic.Anthropic()

    prompt = f"""
Today's mortgage rate data:
{rates_text}

Rishi's current rate: {MY_MORTGAGE['current_rate']}%
Current balance: ${MY_MORTGAGE['current_balance']:,}
Monthly interest: ${MY_MORTGAGE['monthly_interest']}
ARM adjusts in: {MY_MORTGAGE['arm_adjusts_in']}
Refi threshold: 15yr below {MY_MORTGAGE['refi_action_threshold']}%

Respond ONLY with the JSON object. No other text.
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())