#!/usr/bin/env python3
import os, sys, json, pandas as pd, requests
from dotenv import load_dotenv

# Load configuration
try:
    # Try to load from environment file first
    if os.path.exists('config.env'):
        load_dotenv('config.env')
        
    # Import from config.py, allowing environment variables to override
    from config import (
        INPUT_XLS as DEFAULT_INPUT_XLS,
        OUTPUT_FILE as DEFAULT_OUTPUT_FILE,
        BASE_URL as DEFAULT_BASE_URL,
        API_KEY as DEFAULT_API_KEY,
        MODEL as DEFAULT_MODEL,
        TEMPERATURE as DEFAULT_TEMPERATURE,
        MAX_TOKENS as DEFAULT_MAX_TOKENS,
        REQUEST_TIMEOUT as DEFAULT_REQUEST_TIMEOUT,
        CONNECTION_TIMEOUT as DEFAULT_CONNECTION_TIMEOUT
    )
    
    # Use environment variables if available, otherwise use config.py defaults
    INPUT_XLS = os.getenv('INPUT_XLS', DEFAULT_INPUT_XLS)
    OUTPUT_FILE = os.getenv('OUTPUT_FILE', DEFAULT_OUTPUT_FILE)
    BASE_URL = os.getenv('BASE_URL', DEFAULT_BASE_URL)
    API_KEY = os.getenv('API_KEY', DEFAULT_API_KEY)
    MODEL = os.getenv('MODEL', DEFAULT_MODEL)
    TEMPERATURE = float(os.getenv('TEMPERATURE', DEFAULT_TEMPERATURE))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', DEFAULT_MAX_TOKENS))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', DEFAULT_REQUEST_TIMEOUT))
    CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', DEFAULT_CONNECTION_TIMEOUT))
    
except ImportError:
    print("[ERROR] config.py not found. Please create config.py with your settings.")
    sys.exit(1)

print(f"🔧 Configuration loaded:")
print(f"   Input file: {INPUT_XLS}")
print(f"   Output file: {OUTPUT_FILE}")
print(f"   API endpoint: {BASE_URL}")
print(f"   Model: {MODEL}")
print(f"   API key: {'Set' if API_KEY else 'Not set (local model)'}")

SYSTEM_PROMPT = '''You are an organisational psychologist specialising in digital psychometrics.
Evaluate the LinkedIn post provided by the USER and return ONLY valid JSON that follows the exact schema shown below.

CRITICAL: Your response must contain ONLY the JSON object. No explanations, no markdown formatting, no thinking process, no extra text whatsoever.

Scoring rules (1 very low → 5 very high).

────────────────────────────────────────
Topic-tag categories (controlled vocab)
────────────────────────────────────────
Choose up to **three** categories that fit the post and list them in the
"topic_tags" array (JSON list of strings).  If none apply, use ["Other"].

- "AI technical deep dive"        (algorithms, LLM internals, code)
- "AI tools & workflows"          (applications, prompts, use-cases)
- "Prompt engineering"            (prompt craft, guard-rails, best-practices)
- "LinkedIn growth strategy"      (content pillars, audience building)
- "LinkedIn automation"           (scraping, APIs, DM sequences, growth hacks)
- "SaaS product strategy"         (pricing, GTM, roadmap, metrics)
- "SaaS engineering & integr."    (architecture, MLOps, MCP, APIs)
- "Growth marketing"              (funnels, paid/organic, CRO)
- "Personal branding"             (storytelling, visibility, career narrative)
- "Leadership & culture"          (team, vision, values)
- "Entrepreneurship & funding"    (fund-raise, equity, exits, finance)
- "Productivity & learning"       (workflows, study hacks, tooling)
- "Other"

────────────────────────────────────────
SCHEMA:
{
  "topic_tags": [ "" ],          // ≤3 strings from the list above
  "big_five": {
    "openness": <int 1-5>,
    "conscientiousness": <int 1-5>,
    "extraversion": <int 1-5>,
    "agreeableness": <int 1-5>,
    "neuroticism": <int 1-5>
  },
  "partner_traits": {
    "integrity_trust":    <int 1-5>,
    "reliability":        <int 1-5>,
    "collaboration":      <int 1-5>,
    "adaptability":       <int 1-5>,
    "risk_tolerance":     <int 1-5>,
    "strategic_thinking": <int 1-5>,
    "leadership":         <int 1-5>
  },
  "flags": {
    "self_promotion":      <boolean>,
    "humility":            <boolean>,
    "controversial":       <boolean>,
    "aggressive_language": <boolean>
  },
  "evidence": {
    "integrity_trust":    "<string>",
    "reliability":        "<string>",
    "collaboration":      "<string>",
    "adaptability":       "<string>",
    "risk_tolerance":     "<string>",
    "strategic_thinking": "<string>",
    "leadership":         "<string>"
  }
}

Respond with _only_ the JSON object.
'''

CHAT_ENDPOINT = f"{BASE_URL}/chat/completions"
HEADERS = {"Content-Type": "application/json"}

# Add API key to headers if provided
if API_KEY:
    HEADERS["Authorization"] = f"Bearer {API_KEY}"


def load_posts(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Excel file not found: {path}")
    
    df = pd.read_excel(path, header=None, engine="openpyxl")
    # first column = col 0, posts start at Excel row 3 → df.iloc[2:]
    posts = df.iloc[2:, 0].dropna()
    
    if posts.empty:
        raise ValueError("No posts found in the Excel file")
    
    return posts


def load_done_ids(path):
    done = set()
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    pid = obj.get("post_id")
                    if pid:
                        done.add(pid)
                except json.JSONDecodeError:
                    continue
    return done


def clean_json_response(response_text):
    """Extract JSON from LLM response, handling cases where extra text is included."""
    response_text = response_text.strip()
    
    # Remove any thinking tags or similar
    if "<think>" in response_text and "</think>" in response_text:
        start = response_text.find("</think>") + len("</think>")
        response_text = response_text[start:].strip()
    
    # Look for JSON object boundaries
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    
    if json_start != -1 and json_end > json_start:
        return response_text[json_start:json_end]
    
    return response_text


def call_llm(post_text):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": str(post_text)}
        ],
        "temperature": TEMPERATURE,
        "max_tokens":  MAX_TOKENS
    }
    r = requests.post(CHAT_ENDPOINT, headers=HEADERS, json=payload, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    resp = r.json()
    raw_response = resp["choices"][0]["message"]["content"]
    return clean_json_response(raw_response)


def main():
    try:
        posts = load_posts(INPUT_XLS)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    
    done_ids = load_done_ids(OUTPUT_FILE)
    
    # Test API connection
    try:
        test_response = requests.get(f"{BASE_URL}/models", headers=HEADERS if API_KEY else {}, timeout=CONNECTION_TIMEOUT)
        test_response.raise_for_status()
        print(f"✅ Connected to API at {BASE_URL}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Cannot connect to API at {BASE_URL}: {e}")
        if not API_KEY:
            print("Make sure LM Studio is running and the server is started.")
        else:
            print("Check your API key and endpoint configuration.")
        sys.exit(1)

    total_posts = len(posts)
    processed_count = len(done_ids)
    print(f"📊 Found {total_posts} posts, {processed_count} already processed")

    for idx, post in posts.items():
        excel_row = str(idx + 1)  # Excel row number (df starts from row 2, +1 for 1-indexed Excel)
        if excel_row in done_ids:
            continue

        processed_count += 1
        print(f"→ Processing row {excel_row} ({processed_count}/{total_posts})...")
        
        try:
            reply = call_llm(post)
        except Exception as e:
            print(f"[ERROR] LLM call failed on row {excel_row}: {e}")
            print("Continuing with next post...")
            continue

        try:
            obj = json.loads(reply)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON on row {excel_row}: {e}")
            print("Raw response:")
            print(reply)
            print("Continuing with next post...")
            continue

        # Add post_id as a separate field for tracking
        obj["post_id"] = excel_row

        # Save immediately and flush to disk
        with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            out.flush()  # Force write to disk
        
        print(f"✅ Saved result for row {excel_row}")

    print(f"🎉 All done! Processed {processed_count} posts. Results are in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
