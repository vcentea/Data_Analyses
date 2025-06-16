#!/usr/bin/env python3
import os, sys, json, pandas as pd, requests
import argparse
from dotenv import load_dotenv

# Load configuration
try:
    # Try to load from environment file first
    if os.path.exists('config.env'):
        load_dotenv('config.env')
    elif os.path.exists('../config.env'):
        load_dotenv('../config.env')
        
    # Import from config.py, allowing environment variables to override
    try:
        from config import (
            OUTPUT_FILE as DEFAULT_OUTPUT_FILE,
            BASE_URL as DEFAULT_BASE_URL,
            API_KEY as DEFAULT_API_KEY,
            MODEL as DEFAULT_MODEL,
            TEMPERATURE as DEFAULT_TEMPERATURE,
            MAX_TOKENS as DEFAULT_MAX_TOKENS,
            REQUEST_TIMEOUT as DEFAULT_REQUEST_TIMEOUT,
            CONNECTION_TIMEOUT as DEFAULT_CONNECTION_TIMEOUT
        )
    except ImportError:
        # Try importing from parent directory
        sys.path.append('..')
        from config import (
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
print(f"   Output file: {OUTPUT_FILE}")
print(f"   API endpoint: {BASE_URL}")
print(f"   Model: {MODEL}")
print(f"   API key: {'Set' if API_KEY else 'Not set (local model)'}")

# Token tracking globals
total_input_tokens = 0
total_output_tokens = 0
total_thinking_tokens = 0
total_requests = 0

SYSTEM_PROMPT = '''You are an organisational psychologist specialising in digital psychometrics.
Evaluate the LinkedIn post provided by the USER and return ONLY valid JSON that follows the exact schema shown below.

CRITICAL: Your response must contain ONLY the JSON object. No explanations, no markdown formatting, no extra text whatsoever.


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


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process LinkedIn posts from Excel file for psychometric analysis")
    parser.add_argument("input_file", help="Path to the Excel file containing LinkedIn posts")
    parser.add_argument("-o", "--output", default=OUTPUT_FILE, help=f"Output JSONL file (default: {OUTPUT_FILE})")
    return parser.parse_args()


def load_posts(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Excel file not found: {path}")
    
    df = pd.read_excel(path, engine="openpyxl")
    
    # Check if this is the vlad format (has post_text column) or charlie format (no headers)
    if 'post_text' in df.columns:
        # Vlad format: use post_text column and post_number for ID
        posts_data = df[['post_number', 'post_text']].dropna(subset=['post_text'])
        if posts_data.empty:
            raise ValueError("No posts found in the post_text column")
        return posts_data
    else:
        # Charlie format: first column contains posts, starting from row 3
        posts = df.iloc[2:, 0].dropna()
        if posts.empty:
            raise ValueError("No posts found in the Excel file")
        # Convert to same format as vlad for consistency
        posts_data = pd.DataFrame({
            'post_number': range(1, len(posts) + 1),
            'post_text': posts.values
        })
        posts_data.index = posts.index  # Keep original index for excel_row calculation
        return posts_data


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
    global total_input_tokens, total_output_tokens, total_thinking_tokens, total_requests
    
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
    
    # Extract token usage if available
    usage = resp.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    thinking_tokens = usage.get("reasoning_tokens", 0)  # For models with thinking/reasoning
    
    # Update totals
    total_input_tokens += input_tokens
    total_output_tokens += output_tokens
    total_thinking_tokens += thinking_tokens
    total_requests += 1
    
    return clean_json_response(raw_response), input_tokens, output_tokens, thinking_tokens


def print_token_summary():
    """Print final token usage summary"""
    print("\n" + "="*60)
    print("📊 TOKEN USAGE SUMMARY")
    print("="*60)
    print(f"Total requests processed: {total_requests}")
    print(f"Total input tokens:       {total_input_tokens:,}")
    print(f"Total output tokens:      {total_output_tokens:,}")
    if total_thinking_tokens > 0:
        print(f"Total thinking tokens:    {total_thinking_tokens:,}")
    print(f"Total tokens:             {total_input_tokens + total_output_tokens + total_thinking_tokens:,}")
    print("-"*60)
    if total_requests > 0:
        avg_input = total_input_tokens / total_requests
        avg_output = total_output_tokens / total_requests
        avg_thinking = total_thinking_tokens / total_requests
        print(f"Average input per post:   {avg_input:.1f} tokens")
        print(f"Average output per post:  {avg_output:.1f} tokens")
        if total_thinking_tokens > 0:
            print(f"Average thinking per post: {avg_thinking:.1f} tokens")
    print("="*60)


def main():
    args = parse_arguments()
    
    try:
        posts_data = load_posts(args.input_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    
    done_ids = load_done_ids(args.output)
    
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

    total_posts = len(posts_data)
    processed_count = len(done_ids)
    print(f"📊 Found {total_posts} posts, {processed_count} already processed")

    for idx, row in posts_data.iterrows():
        post_number = str(int(row['post_number']))  # Use post_number as ID
        post_text = row['post_text']
        
        if post_number in done_ids:
            continue

        processed_count += 1
        print(f"→ Processing post {post_number} ({processed_count}/{total_posts})...")
        
        try:
            reply, input_tokens, output_tokens, thinking_tokens = call_llm(post_text)
            if thinking_tokens > 0:
                print(f"  📈 Tokens: {input_tokens} in → {output_tokens} out → {thinking_tokens} thinking")
            else:
                print(f"  📈 Tokens: {input_tokens} in → {output_tokens} out")
        except Exception as e:
            print(f"[ERROR] LLM call failed on post {post_number}: {e}")
            print("Continuing with next post...")
            continue

        try:
            obj = json.loads(reply)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON on post {post_number}: {e}")
            print("Raw response:")
            print(reply)
            print("Continuing with next post...")
            continue

        # Add post_id as a separate field for tracking
        obj["post_id"] = post_number

        # Save immediately and flush to disk
        with open(args.output, "a", encoding="utf-8") as out:
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            out.flush()  # Force write to disk
        
        print(f"✅ Saved result for post {post_number}")

    print(f"🎉 All done! Processed {processed_count} posts. Results are in {args.output}")
    
    # Print token usage summary
    print_token_summary()


if __name__ == "__main__":
    main()
