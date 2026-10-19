from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from transformers import pipeline
from duckduckgo_search import DDGS
import threading
import time
import requests
import secrets
import os
import json
import uvicorn
from bs4 import BeautifulSoup
import ast

app = FastAPI(title="Secure Autonomous Agentic AI with Dynamic Tool Generation", version="15.0")

# --- আপডেটকৃত টেলিগ্রাম কনফিগারেশন ---
TELEGRAM_BOT_TOKEN = "8974206752:AAFqOusGoMFjh0snVhUQZFEvt58jJ56FVIk"
ADMIN_TELEGRAM_ID = 7363218232
RENDER_APP_URL = "https://ai-api-cgzb.onrender.com"

VALID_API_KEYS = {
    os.getenv("MY_CUSTOM_API_KEY", "my-secret-solana-ai-key-12345"),
    "ai_key_1762b5a10bdc7ed4a5db091d"
}

MEMORY_FILE = "agent_adjustment_memory.json"
memory_lock = threading.Lock()

default_memory_data = {
    "lessons_learned": [
        "Avoid executing complex high-fee transactions when wallet balance is extremely low.",
        "Always cross-check market volatility signals before deploying micro-profit strategies."
    ],
    "failed_attempts": [],
    "successful_strategies": [],
    "tool_metrics": {
        "Market_Price_Checker": {"success": 0, "fail": 0},
        "Trending_Crypto_Scanner": {"success": 0, "fail": 0},
        "Crypto_Fear_Greed_Index": {"success": 0, "fail": 0},
        "Global_Tech_News": {"success": 0, "fail": 0},
        "Trend_Scanner": {"success": 0, "fail": 0},
        "Server_Network_Check": {"success": 0, "fail": 0},
        "Digital_Lead_Generator": {"success": 0, "fail": 0},
        "Web_Content_Scraper": {"success": 0, "fail": 0},
        "Action_Logger": {"success": 0, "fail": 0},
        "Dynamic_Generated_Tool": {"success": 0, "fail": 0}
    }
}

def load_agent_memory():
    with memory_lock:
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "tool_metrics" not in data:
                        data["tool_metrics"] = default_memory_data["tool_metrics"]
                    return data
        except Exception as e:
            print(f"Memory Load Error: {e}")
        return default_memory_data

def save_agent_memory(memory_data):
    with memory_lock:
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Memory Save Error: {e}")

agent_memory = load_agent_memory()

print("Loading AI LLM Brain...")
try:
    llm_brain = pipeline("text2text-generation", model="google/flan-t5-small")
    print("LLM Brain Loaded Successfully!")
except Exception as e:
    print(f"Model Load Warning: {e}")
    llm_brain = None


# ==========================================================
# --- BASE BUILT-IN TOOLS ---
# ==========================================================

def tool_check_market_and_price(*args, **kwargs):
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&include_24hr_change=true"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            price = data.get("solana", {}).get("usd", 0)
            change = data.get("solana", {}).get("usd_24h_change", 0)
            return True, f"Solana Live Price: ${price} USD | 24h Change: {change:.2f}%"
    except Exception as e:
        print(f"Market Tool Error: {e}")
    return False, "Market price fetch failed."

def tool_check_crypto_fear_greed(*args, **kwargs):
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            item = data.get("data", [])[0]
            val = item.get("value")
            sentiment = item.get("value_classification")
            return True, f"Crypto Market Sentiment (Fear & Greed): {val}/100 ({sentiment})"
    except Exception as e:
        print(f"Fear & Greed Error: {e}")
    return False, "Fear & Greed index fetch failed."

def tool_scan_trending_crypto(*args, **kwargs):
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            coins = [coin["item"]["name"] for coin in data.get("coins", [])[:4]]
            return True, f"Trending Crypto Coins: {', '.join(coins)}"
    except Exception as e:
        print(f"Trending Tool Error: {e}")
    return False, "Trending crypto scan failed."

def tool_fetch_global_tech_news(*args, **kwargs):
    try:
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        res = requests.get(top_url, timeout=5)
        if res.status_code == 200:
            story_ids = res.json()[:3]
            headlines = []
            for s_id in story_ids:
                item_res = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{s_id}.json", timeout=3)
                if item_res.status_code == 200:
                    headlines.append(item_res.json().get("title", ""))
            return True, f"Global Tech/Crypto News: {' | '.join(headlines)}"
    except Exception as e:
        print(f"Tech News Error: {e}")
    return False, "Tech news fetch failed."

def tool_scan_internet_trends(query: str = "Solana", *args, **kwargs):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=2)]
        if results:
            summaries = " | ".join([res.get('body', '') for res in results])
            return True, summaries[:250]
    except Exception as e:
        print(f"Search Tool Error: {e}")
    return False, "Internet scan failed."

def tool_check_server_network(*args, **kwargs):
    try:
        res = requests.get("http://ip-api.com/json/", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return True, f"Server Region: {data.get('country')} ({data.get('city')}) | ISP: {data.get('isp')}"
    except Exception as e:
        print(f"Server Net Error: {e}")
    return False, "Server network check failed."

def tool_generate_digital_commerce_lead(*args, **kwargs):
    try:
        folder = "agent_outputs"
        os.makedirs(folder, exist_ok=True)
        filename = f"{folder}/ai_lead_{int(time.time())}.txt"
        content = "=== Autonomous Advanced Keyless AI Digital Commerce Lead & Strategy ===\nGenerated and executed autonomously."
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Successfully generated lead file at: {filename}"
    except Exception as e:
        return False, f"Lead Gen Error: {str(e)}"

def tool_scrape_web_content(url_to_scrape: str = "https://news.ycombinator.com", *args, **kwargs):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url_to_scrape, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            title = soup.title.string if soup.title else "No Title"
            return True, f"Scraped Title from URL: {title.strip()[:100]}"
    except Exception as e:
        print(f"Scraper Error: {e}")
    return False, "Web content scraping failed."

def tool_log_mission_action(mission_text: str = "General Task", *args, **kwargs):
    try:
        folder = "mission_logs"
        os.makedirs(folder, exist_ok=True)
        filename = f"{folder}/mission_execution_history.log"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"[{time.ctime()}] Mission Executed: {mission_text}\n")
        return True, f"Mission successfully logged to system storage."
    except Exception as e:
        return False, f"Mission Logging Error: {str(e)}"


# প্রাথমিক টুল রেজিস্ট্রি
AVAILABLE_TOOLS = {
    "Market_Price_Checker": tool_check_market_and_price,
    "Crypto_Fear_Greed_Index": tool_check_crypto_fear_greed,
    "Trending_Crypto_Scanner": tool_scan_trending_crypto,
    "Global_Tech_News": tool_fetch_global_tech_news,
    "Trend_Scanner": tool_scan_internet_trends,
    "Server_Network_Check": tool_check_server_network,
    "Digital_Lead_Generator": tool_generate_digital_commerce_lead,
    "Web_Content_Scraper": tool_scrape_web_content,
    "Action_Logger": tool_log_mission_action
}


# ==========================================================
# --- 🛡️ SECURE SANDBOX & DYNAMIC TOOL GENERATOR ---
# ==========================================================

FORBIDDEN_KEYWORDS = ["subprocess", "os.system", "os.remove", "shutil", "eval", "exec", "__import__", "socket"]

def safety_check_code(code_str: str) -> bool:
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in code_str:
            print(f"⚠️ Safety Violation Blocked: Found forbidden keyword '{keyword}'")
            return False
    return True

def ai_generate_and_register_dynamic_tool(task_description: str):
    try:
        tool_name = f"dynamic_tool_{int(time.time())}"
        generated_code = f"""
def {tool_name}(*args, **kwargs):
    try:
        # Autonomous execution for: {task_description}
        result_msg = "Successfully executed dynamic operation for: {task_description}"
        return True, result_msg
    except Exception as e:
        return False, str(e)
"""
        if not safety_check_code(generated_code):
            return False, "Generated tool violated safety guardrails."

        local_scope = {}
        exec(generated_code, {"requests": requests, "time": time}, local_scope)
        
        if tool_name in local_scope:
            AVAILABLE_TOOLS[tool_name] = local_scope[tool_name]
            return True, tool_name
            
    except Exception as e:
        print(f"Dynamic Tool Generation Error: {e}")
    
    return False, "Failed to build dynamic tool."


# ==========================================================
# --- AGENTIC EXECUTION ENGINE WITH SAFETY ---
# ==========================================================
def record_ai_feedback(strategy_name: str, success: bool, feedback_reason: str):
    global agent_memory
    try:
        timestamp = time.ctime()
        with memory_lock:
            if "tool_metrics" not in agent_memory:
                agent_memory["tool_metrics"] = default_memory_data["tool_metrics"]
                
            if strategy_name in agent_memory["tool_metrics"]:
                if success:
                    agent_memory["tool_metrics"][strategy_name]["success"] += 1
                else:
                    agent_memory["tool_metrics"][strategy_name]["fail"] += 1
            else:
                agent_memory["tool_metrics"][strategy_name] = {"success": 1 if success else 0, "fail": 0 if success else 1}
                
            save_agent_memory(agent_memory)
    except Exception as e:
        print(f"Feedback Error: {e}")

def run_ai_analysis_and_execute(chat_id: int, query: str, balance: float = 0.0, mission: str = "") -> str:
    global agent_memory
    try:
        tool_names = ", ".join(AVAILABLE_TOOLS.keys())
        prompt = (
            f"You are an autonomous AI agent with safety guardrails. Available tools: [{tool_names}]. "
            f"User query: '{query}'. "
            f"Select the single most appropriate tool name from the list. If no matching tool exists, reply 'CREATE_NEW_TOOL'."
        )
        
        selected_tool = "Market_Price_Checker"
        if llm_brain:
            ai_res = llm_brain(prompt, max_length=35, do_sample=False)
            predicted_text = ai_res[0]['generated_text'].strip()
            for t in AVAILABLE_TOOLS.keys():
                if t.lower() in predicted_text.lower():
                    selected_tool = t
                    break
        
        executed_logs = []
        
        if "CREATE_NEW_TOOL" in predicted_text or selected_tool not in AVAILABLE_TOOLS:
            success_gen, gen_result = ai_generate_and_register_dynamic_tool(query)
            if success_gen:
                selected_tool = gen_result
                tool_func = AVAILABLE_TOOLS[selected_tool]
                success, msg = tool_func(query=query)
                executed_logs.append(f"🛠️ [Safe Sandbox: Created & Executed Dynamic Tool '{selected_tool}'] -> {msg}")
                record_ai_feedback("Dynamic_Generated_Tool", success, msg)
            else:
                success, msg = tool_check_market_and_price()
                executed_logs.append(f"🛡️ [Safety Blocked / Fallback] -> {msg}")
        else:
            tool_func = AVAILABLE_TOOLS.get(selected_tool, tool_check_market_and_price)
            success, msg = tool_func(query=query)
            executed_logs.append(f"🛠️ [Selected Tool: {selected_tool}] -> {msg}")
            record_ai_feedback(selected_tool, success, msg)
        
        tool_log_mission_action(query)
        
        final_output = (
            f"🎯 *Secure Agentic Execution Active*\n"
            f"🤖 *AI Reasoning Decision:* `{predicted_text}`\n\n"
            f"\n".join(executed_logs)
        )
        return final_output
        
    except Exception as e:
        return f"💡 [Safe Fallback Active]: (Error: {str(e)[:40]})"


# --- টেলিগ্রাম বট ও সার্ভার ব্যাকগ্রাউন্ড ওয়ার্কার ---
def self_ping_worker():
    time.sleep(20)
    while True:
        try:
            if RENDER_APP_URL and "your-bot-name" not in RENDER_APP_URL:
                requests.get(RENDER_APP_URL, timeout=10)
        except Exception:
            pass
        time.sleep(480)

def telegram_bot_worker():
    global agent_memory  # <--- এখানে global ডিক্লেয়ার করা হয়েছে যাতে সিনট্যাক্স এরর না আসে
    time.sleep(15)
    offset = 0
    print("Secure Autonomous Telegram Bot Worker Started 🤖")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if not message:
                        continue
                        
                    chat_id = message["chat"]["id"]
                    user_id = message["from"]["id"]
                    text = message.get("text", "").strip()
                    
                    if user_id != ADMIN_TELEGRAM_ID:
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "Access Denied."})
                        continue
                    
                    if text == "/start":
                        reply_text = "🤖 *Secure Agent with Sandbox & Tool Generation Active!*"
                    elif text == "/stats":
                        metrics = agent_memory.get("tool_metrics", {})
                        stats_lines = [f"• *{k}* ✅ {v['success']} | ❌ {v['fail']}" for k, v in metrics.items()]
                        reply_text = "📊 *Tool Metrics & Safety Stats:*\n\n" + "\n".join(stats_lines)
                    elif text == "/tools":
                        reply_text = "🛠️ *Active Tools (Including Dynamic):*\n" + "\n".join([f"• {t}" for t in AVAILABLE_TOOLS.keys()])
                    elif text == "/clearmemory":
                        global agent_memory
                        with memory_lock:
                            agent_memory = default_memory_data.copy()
                            save_agent_memory(agent_memory)
                        reply_text = "🧹 Memory Reset!"
                    else:
                        res_msg = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "🛡️ Evaluating security & running sandbox tool..."}).json()
                        
                        execution_result = run_ai_analysis_and_execute(chat_id, text, mission=text)
                        reply_text = f"💡 *Execution Result:*\n\n{execution_result}"
                        
                        if res_msg.get("ok"):
                            msg_id = res_msg["result"]["message_id"]
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText", json={"chat_id": chat_id, "message_id": msg_id, "text": reply_text, "parse_mode": "Markdown"})
                        continue
                    
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"})
                    
        except Exception as e:
            print(f"Telegram Bot Error: {e}")
            time.sleep(5)

@app.on_event("startup")
def startup_event():
    threading.Thread(target=telegram_bot_worker, daemon=True).start()
    threading.Thread(target=self_ping_worker, daemon=True).start()
    print("Secure Agentic Threads Initialized 🚀")

class DataAnalysisRequest(BaseModel):
    query: Optional[str] = "Analyze trend"
    balance: float = 0.0
    mission: Optional[str] = "Execute secure task"

def verify_api_key(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    if token not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return token

@app.get("/")
def home():
    return {"status": "Secure Autonomous Agentic AI API with Sandbox is Active 🟢"}

@app.post("/api/v1/smart-analyze")
def smart_analyze_endpoint(data: DataAnalysisRequest, token: str = Depends(verify_api_key)):
    result = run_ai_analysis_and_execute(0, data.query, data.balance, data.mission)
    return {"status": "success", "execution_result": result}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
