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

app = FastAPI(title="Autonomous Agentic AI API with Advanced Keyless Tools & Metrics", version="12.1")

# টেলিগ্রাম কনফিগারেশন (অক্ষুণ্ণ রাখা হয়েছে)
TELEGRAM_BOT_TOKEN = "8931678358:AAEFHNA__FVJlwB6LGbkYRFPXVMm7fYBaaA"
ADMIN_TELEGRAM_ID = 7363218232

# রেন্ডার ওয়েব সার্ভারের পাবলিক লিঙ্ক
RENDER_APP_URL = "https://ai-api-cgzb.onrender.com"

# এপিআই কি ভ্যালিডেশন
VALID_API_KEYS = {
    os.getenv("MY_CUSTOM_API_KEY", "my-secret-solana-ai-key-12345"),
    "ai_key_1762b5a10bdc7ed4a5db091d"
}

# --- পার্সিস্টেন্ট মেমরি ফাইল এবং মেট্রিক্স ডেটাবেজ সেটআপ ---
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
        "Digital_Lead_Generator": {"success": 0, "fail": 0}
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

# Hugging Face থেকে হালকা মডেল লোড করা
print("Loading AI LLM Brain...")
try:
    llm_brain = pipeline("text2text-generation", model="google/flan-t5-small")
    print("LLM Brain Loaded Successfully!")
except Exception as e:
    print(f"Model Load Warning: {e}")
    llm_brain = None


# ==========================================================
# --- ADVANCED KEYLESS FREE PUBLIC TOOLS (উন্নত ফ্রি টুলস) ---
# ==========================================================

def tool_check_market_and_price():
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

def tool_check_crypto_fear_greed():
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

def tool_scan_trending_crypto():
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

def tool_fetch_global_tech_news():
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

def tool_scan_internet_trends(query: str):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=2)]
        if results:
            summaries = " | ".join([res.get('body', '') for res in results])
            return True, summaries[:250]
    except Exception as e:
        print(f"Search Tool Error: {e}")
    return False, "Internet scan failed."

def tool_check_server_network():
    try:
        res = requests.get("http://ip-api.com/json/", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return True, f"Server Region: {data.get('country')} ({data.get('city')}) | ISP: {data.get('isp')}"
    except Exception as e:
        print(f"Server Net Error: {e}")
    return False, "Server network check failed."

def tool_generate_digital_commerce_lead():
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


# ==========================================================
# --- SMART AGENTIC TOOL DISPATCHER WITH METRICS TRACKING ---
# ==========================================================
def autonomous_tool_dispatcher(ai_decision_text: str, query: str):
    executed_logs = []
    combined_text = (ai_decision_text + " " + query).lower()
    
    if "price" in combined_text or "market" in combined_text or "solana" in combined_text or "balance" in combined_text:
        success, msg = tool_check_market_and_price()
        executed_logs.append(f"🛠️ [Tool: Market Price] -> {msg}")
        record_ai_feedback("Market_Price_Checker", success, msg)
        
    if "sentiment" in combined_text or "fear" in combined_text or "greed" in combined_text or "crypto" in combined_text:
        success, msg = tool_check_crypto_fear_greed()
        executed_logs.append(f"🛠️ [Tool: Fear & Greed Index] -> {msg}")
        record_ai_feedback("Crypto_Fear_Greed_Index", success, msg)
        
    if "trending" in combined_text or "coin" in combined_text or "token" in combined_text:
        success, msg = tool_scan_trending_crypto()
        executed_logs.append(f"🛠️ [Tool: Trending Crypto] -> {msg}")
        record_ai_feedback("Trending_Crypto_Scanner", success, msg)
        
    if "news" in combined_text or "tech" in combined_text or "global" in combined_text:
        success, msg = tool_fetch_global_tech_news()
        executed_logs.append(f"🛠️ [Tool: Global Tech News] -> {msg}")
        record_ai_feedback("Global_Tech_News", success, msg)
        
    if "scan" in combined_text or "trend" in combined_text or "signal" in combined_text or "strategy" in combined_text:
        success, msg = tool_scan_internet_trends(query)
        executed_logs.append(f"🛠️ [Tool: DDGS Trend Scan] -> {msg}")
        record_ai_feedback("Trend_Scanner", success, msg)
        
    if "server" in combined_text or "network" in combined_text or "ip" in combined_text:
        success, msg = tool_check_server_network()
        executed_logs.append(f"🛠️ [Tool: Server Network] -> {msg}")
        record_ai_feedback("Server_Network_Check", success, msg)
        
    if "lead" in combined_text or "commerce" in combined_text or "generate" in combined_text or "zero balance" in combined_text:
        success, msg = tool_generate_digital_commerce_lead()
        executed_logs.append(f"🛠️ [Tool: Lead Generator] -> {msg}")
        record_ai_feedback("Digital_Lead_Generator", success, msg)
        
    if not executed_logs:
        s1, m1 = tool_check_market_and_price()
        s2, m2 = tool_check_crypto_fear_greed()
        executed_logs.append(f"🛠️ [Default Tools Executed] -> {m1} | {m2}")
        record_ai_feedback("Market_Price_Checker", s1, m1)
        record_ai_feedback("Crypto_Fear_Greed_Index", s2, m2)
        
    return "\n".join(executed_logs)


# ==========================================================
# --- LLM ADJUSTMENT LOOP & REASONING ENGINE ---
# ==========================================================
def run_ai_analysis_and_execute(chat_id: int, query: str, balance: float = 0.0, mission: str = "") -> str:
    global agent_memory
    try:
        recent_lessons = agent_memory.get("lessons_learned", [])
        lessons_text = "\n".join([f"⚠️ Past Lesson {i+1}: {lesson}" for i, lesson in enumerate(recent_lessons[-4:])]) if recent_lessons else "No prior lessons recorded."
        
        extra_context = f"Wallet Balance: {balance} SOL\n"
        if mission:
            extra_context += f"Active Mission: {mission}\n"
            
        structured_prompt = (
            f"{extra_context}"
            f"🧠 [SELF-CORRECTION LESSONS]:\n{lessons_text}\n\n"
            f"Objective: {query}\n"
            f"Instructions: Analyze market sentiment and decide the best automated action.\n"
            f"Decision Strategy:"
        )
        
        if llm_brain:
            ai_output = llm_brain(structured_prompt, max_length=130, do_sample=False)
            ai_decision = ai_output[0]['generated_text']
        else:
            ai_decision = "Check market price, evaluate fear & greed sentiment, and scan trending crypto."
            
        tool_execution_results = autonomous_tool_dispatcher(ai_decision, query)
        
        final_output = (
            f"🤖 *AI Strategic Decision:* {ai_decision}\n\n"
            f"{tool_execution_results}"
        )
        return final_output
        
    except Exception as e:
        return f"💡 [Resilient Fallback Execution Active]: (Error: {str(e)[:30]})"


# --- ফিডব্যাক ও মেট্রিক্স আপডেট করার ফাংশন ---
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
                    
            if success:
                agent_memory["successful_strategies"].append({
                    "strategy": strategy_name,
                    "timestamp": timestamp,
                    "note": feedback_reason
                })
            else:
                agent_memory["failed_attempts"].append({
                    "strategy": strategy_name,
                    "reason": feedback_reason,
                    "timestamp": timestamp
                })
                new_lesson = f"Failed in '{strategy_name}' due to: {feedback_reason}. Avoid this in future cycles."
                if new_lesson not in agent_memory["lessons_learned"]:
                    agent_memory["lessons_learned"].append(new_lesson)
                    
            save_agent_memory(agent_memory)
        return True
    except Exception as e:
        print(f"Feedback Recording Error: {e}")
        return False


# --- রেন্ডার ফ্রি সার্ভার স্লিপ রোধ করার অ্যান্টি-স্লিপ ওয়ার্কার ---
def self_ping_worker():
    time.sleep(20)
    print("Anti-Sleep Self-Ping Worker Started 🟢")
    while True:
        try:
            if RENDER_APP_URL and "your-bot-name" not in RENDER_APP_URL:
                requests.get(RENDER_APP_URL, timeout=10)
        except Exception:
            pass
        time.sleep(480)


# --- টেলিগ্রাম বট ব্যাকগ্রাউন্ড ওয়ার্কার ---
def telegram_bot_worker():
    time.sleep(15)
    offset = 0
    print("Advanced Autonomous Telegram Bot Worker Started 🤖")
    
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
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                            json={"chat_id": chat_id, "text": "Access Denied - অনুমতিপ্রাপ্ত ব্যবহারকারী নন।"}
                        )
                        continue
                    
                    if text == "/generatekey":
                        new_key = f"ai_key_{secrets.token_hex(12)}"
                        VALID_API_KEYS.add(new_key)
                        reply_text = f"🔑 নতুন এপিআই কি জেনারেট করা হয়েছে:\n\n`{new_key}`"
                    
                    elif text in ["/start", "/help"]:
                        lessons_count = len(agent_memory.get("lessons_learned", []))
                        reply_text = (
                            "🤖 *অ্যাডভান্সড অটোনমাস এজেন্টিক এআই বট সক্রিয়!*\n\n"
                            f"🧠 মেমরিতে সংরক্ষিত শিক্ষা: `{lessons_count}টি`\n"
                            "🛠️ এটি এখন মার্কেট প্রাইস, ফিয়ার অ্যান্ড গ্রিড সেন্টিমেন্ট, ট্রেন্ডিং কয়েন, গ্লোবাল নিউজ ও সার্ভার চেক করতে পারে।\n\n"
                            "📌 `/stats` - টুলগুলোর সফলতার পরিসংখ্যান দেখতে\n"
                            "📌 `/memory` - এআই কী শিখল দেখতে\n"
                            "📌 `/tools` - উপলব্ধ ফ্রি টুলস তালিকা\n"
                            "📌 `/clearmemory` - মেমরি রিসেট করতে\n"
                            "📌 যেকোনো কমান্ড বা বিষয় লিখে পাঠান।"
                        )
                    
                    elif text == "/stats":
                        metrics = agent_memory.get("tool_metrics", {})
                        stats_lines = []
                        for t_name, counts in metrics.items():
                            stats_lines.append(f"• *{t_name}* ✅ {counts['success']} | ❌ {counts['fail']}")
                        stats_str = "\n".join(stats_lines) if stats_lines else "কোনো মেট্রিক্স নেই।"
                        reply_text = f"📊 *টুল এক্সিকিউশন পরিসংখ্যান (Metrics):*\n\n{stats_str}"
                    
                    elif text == "/tools":
                        reply_text = (
                            "🛠️ *উপলব্ধ ফ্রি কি-লেস টুলসসমূহ:*\n\n"
                            "1️⃣ Market Price Checker (CoinGecko)\n"
                            "2️⃣ Crypto Fear & Greed Index (Alternative.me)\n"
                            "3️⃣ Trending Crypto Scanner (CoinGecko)\n"
                            "4️⃣ Global Tech News (Hacker News)\n"
                            "5️⃣ DDGS Internet Trend Scanner\n"
                            "6️⃣ Server Network & IP Diagnostic\n"
                            "7️⃣ Digital Commerce Lead Generator"
                        )
                    
                    elif text == "/memory":
                        lessons = agent_memory.get("lessons_learned", [])
                        lessons_str = "\n".join([f"• {l}" for l in lessons[-5:]]) if lessons else "কোনো শিক্ষা জমা নেই।"
                        reply_text = f"🧠 *এআই-এর শেখা পাঠসমূহ:*\n\n{lessons_str}"
                    
                    elif text == "/clearmemory":
                        global agent_memory
                        with memory_lock:
                            agent_memory = default_memory_data.copy()
                            save_agent_memory(agent_memory)
                        reply_text = "🧹 মেমরি ও মেট্রিক্স রিসেট করা হয়েছে!"
                    
                    else:
                        res_msg = requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                            json={"chat_id": chat_id, "text": "🔄 বাজার সেন্টিমেন্ট ও ফ্রি টুলস বিশ্লেষণ করা হচ্ছে..."}
                        ).json()
                        
                        execution_result = run_ai_analysis_and_execute(chat_id, text)
                        
                        reply_text = f"💡 *এআই ডিসিশন ও অ্যাডভান্সড টুল এক্সিকিউশন:*\n\n{execution_result}"
                        if res_msg.get("ok"):
                            msg_id = res_msg["result"]["message_id"]
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText",
                                json={"chat_id": chat_id, "message_id": msg_id, "text": reply_text, "parse_mode": "Markdown"}
                            )
                        continue
                    
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"}
                    )
                    
        except Exception as e:
            print(f"Telegram Bot Error: {e}")
            time.sleep(5)


@app.on_event("startup")
def startup_event():
    bot_thread = threading.Thread(target=telegram_bot_worker, daemon=True)
    bot_thread.start()
    
    ping_thread = threading.Thread(target=self_ping_worker, daemon=True)
    ping_thread.start()
    print("Advanced Autonomous Agentic & Anti-Sleep Threads Initialized 🚀")


# --- ডাটা মডেলসমূহ ---
class DataAnalysisRequest(BaseModel):
    query: Optional[str] = "Analyze Solana trend and market sentiment."
    balance: float = 0.0
    mission: Optional[str] = "Advanced keyless autonomous scanning"

class FeedbackRequest(BaseModel):
    strategy_name: str
    success: bool
    reason: str


def verify_api_key(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    if token not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key - অ্যাক্সেস ডিনাইড")
    return token

@app.get("/")
def home():
    return {"status": "Autonomous Advanced Keyless AI API is Active 🟢"}

@app.post("/api/v1/smart-analyze")
def smart_analyze_and_execute_endpoint(data: DataAnalysisRequest, token: str = Depends(verify_api_key)):
    try:
        result = run_ai_analysis_and_execute(0, data.query or "Solana strategy", data.balance, data.mission or "")
        return {
            "status": "success",
            "engine": "Autonomous AI with Advanced Keyless Tools & Metrics",
            "lessons_applied_count": len(agent_memory.get("lessons_learned", [])),
            "execution_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/v1/log-feedback")
def log_feedback(data: FeedbackRequest, token: str = Depends(verify_api_key)):
    success = record_ai_feedback(data.strategy_name, data.success, data.reason)
    if success:
        return {"status": "success", "message": "Feedback recorded, metrics and lessons updated!"}
    raise HTTPException(status_code=500, detail="Failed to record feedback.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
