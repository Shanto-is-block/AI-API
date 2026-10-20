from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from transformers import pipeline
import threading
import time
import requests
import os
import json
import uvicorn
import ast
import random

app = FastAPI(title="Ultimate Autonomous Crypto Brain & Agent System", version="24.0")

# --- টেলিগ্রাম ও সিস্টেম কনফিগারেশন ---
TELEGRAM_BOT_TOKEN = "8974206752:AAFqOusGoMFjh0snVhUQZFEvt58jJ56FVIk"
ADMIN_TELEGRAM_ID = 7363218232
RENDER_APP_URL = "https://ai-api-cgzb.onrender.com"

VALID_API_KEYS = {
    os.getenv("MY_CUSTOM_API_KEY", "my-secret-solana-ai-key-12345"),
    "ai_key_1762b5a10bdc7ed4a5db091d"
}

# --- 🌐 মেমোরি ও ক্লাউড সিংক কনফিগারেশন ---
LOCAL_MEMORY_FILE = "agent_adjustment_memory.json"
NPOINT_BIN_CONFIG = "npoint_bin.json"
memory_lock = threading.Lock()

default_memory_data = {
    "mode": "virtual",  # "virtual" অথবা "real"
    "real_system_endpoint": "https://your-real-trading-body-url.com/api/execute",
    "real_system_api_key": "your-real-system-secret-key",
    "gemini_keys": [],  # একাধিক জেমিনি এপিআই কি সংরক্ষণের লিস্ট
    "wallet": {
        "balance_usd": 1000.0,
        "crypto_holding": 0.0,
        "total_trades": 0,
        "successful_trades": 0,
        "failed_trades": 0,
        "trade_history": []
    },
    "lessons_learned": [
        "Avoid high leverage or large buys during extreme market fear.",
        "Cross-check 24h momentum and web news sentiment before automated trade triggers.",
        "Only switch to real execution if virtual success rate is above 70%."
    ],
    "tool_metrics": {
        "Market_Price_Checker": {"success": 0, "fail": 0},
        "Simulated_Crypto_Trader": {"success": 0, "fail": 0},
        "Gemini_API_Manager": {"success": 0, "fail": 0},
        "System_API_Access_Module": {"success": 0, "fail": 0},
        "Crypto_Fear_Greed_Index": {"success": 0, "fail": 0},
        "Crypto_News_Sentiment_Analyzer": {"success": 0, "fail": 0}
    }
}

def get_npoint_bin_id():
    if os.path.exists(NPOINT_BIN_CONFIG):
        try:
            with open(NPOINT_BIN_CONFIG, "r") as f:
                return json.load(f).get("bin_id")
        except:
            pass
    return None

def save_npoint_bin_id(bin_id):
    try:
        with open(NPOINT_BIN_CONFIG, "w") as f:
            json.dump({"bin_id": bin_id}, f)
    except:
        pass

def load_agent_memory():
    with memory_lock:
        if os.path.exists(LOCAL_MEMORY_FILE):
            try:
                with open(LOCAL_MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in default_memory_data.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception as e:
                print(f"Local Memory Load Error: {e}")

        bin_id = get_npoint_bin_id()
        if bin_id:
            try:
                res = requests.get(f"https://api.npoint.io/{bin_id}", timeout=6)
                if res and res.status_code == 200:
                    cloud_data = res.json()
                    if "wallet" in cloud_data:
                        with open(LOCAL_MEMORY_FILE, "w", encoding="utf-8") as f:
                            json.dump(cloud_data, f, ensure_ascii=False, indent=4)
                        return cloud_data
            except Exception as e:
                print(f"Cloud Memory Sync Error: {e}")

        return default_memory_data

def save_agent_memory(memory_data):
    with memory_lock:
        try:
            with open(LOCAL_MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Local Memory Save Error: {e}")

        try:
            bin_id = get_npoint_bin_id()
            if not bin_id:
                res = requests.post("https://api.npoint.io", json=memory_data, timeout=6)
                if res and res.status_code in [200, 201]:
                    new_id = res.json().get("id")
                    if new_id:
                        save_npoint_bin_id(new_id)
            else:
                requests.put(f"https://api.npoint.io/{bin_id}", json=memory_data, timeout=6)
        except Exception as e:
            print(f"Cloud Backup Sync Error: {e}")

agent_memory = load_agent_memory()

print("Loading Local AI LLM Brain...")
try:
    llm_brain = pipeline("text2text-generation", model="google/flan-t5-small")
    print("Local LLM Brain Loaded Successfully!")
except Exception as e:
    print(f"Model Load Warning: {e}")
    llm_brain = None


# ==========================================================
# --- 🧠 UNIVERSAL MEMORY PROMPT & CROSS-AI COORDINATOR ---
# ==========================================================

def validate_and_test_gemini_key(api_key: str) -> tuple[bool, str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": "ping test"}]}]}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        if response.status_code == 200:
            return True, "API Key is valid and active."
        else:
            try:
                err_data = response.json()
                msg = err_data.get("error", {}).get("message", "Unknown error")
            except:
                msg = response.text
            
            if response.status_code in [400, 403]:
                return False, f"Invalid or Forbidden Key ({msg})"
            elif response.status_code == 429:
                return False, f"Quota Exceeded / Rate Limit ({msg})"
            else:
                return False, f"Error {response.status_code}: {msg}"
    except Exception as e:
        return False, f"Connection Failed: {str(e)}"

def build_universal_memory_prompt(query: str) -> str:
    """সকল এআই ইঞ্জিনের জন্য মেমোরি, লেসন ও স্ট্যাটস একত্রিত করে একটি সমৃদ্ধ প্রম্পট তৈরি করবে"""
    global agent_memory
    lessons = agent_memory.get("lessons_learned", [])
    wallet = agent_memory.get("wallet", {})
    metrics = agent_memory.get("tool_metrics", {})
    
    lessons_str = "\n".join([f"• {l}" for l in lessons])
    metrics_str = ", ".join([f"{k} (Success:{v['success']}/Fail:{v['fail']})" for k, v in metrics.items()])
    
    prompt = (
        f"[Autonomous Crypto Agent Core Context]\n"
        f"User Command: '{query}'\n"
        f"Portfolio State: Cash ${wallet.get('balance_usd', 0):.2f}, Holdings {wallet.get('crypto_holding', 0):.4f} SOL\n"
        f"Trade History Stats: Total Trades {wallet.get('total_trades', 0)} (Successful: {wallet.get('successful_trades', 0)}, Failed: {wallet.get('failed_trades', 0)})\n"
        f"Learned Lessons & Rules:\n{lessons_str}\n"
        f"Tool Performance Metrics: {metrics_str}\n"
        f"Instruction: Analyze the command using the above historical context and lessons to formulate the smartest strategy."
    )
    return prompt

def ask_ai_with_universal_fallback(query: str) -> tuple[str, str]:
    """যেকোনো এআই (জেমিনি বা লোকাল) এই ফাংশনের মাধ্যমে মেমোরি পড়ে সিদ্ধান্ত নেবে"""
    global agent_memory
    keys = agent_memory.get("gemini_keys", [])
    universal_prompt = build_universal_memory_prompt(query)
    
    # ১. প্রথমে সেভ করা জেমিনি কি (Multi-Key Rotation) দিয়ে চেষ্টা করা
    for key in keys:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": universal_prompt}]}]}
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if text_out:
                        return text_out, "🟢 Gemini API (Cloud Cloud - Memory Aware)"
        except Exception as e:
            continue
            
    # ২. জেমিনি কাজ না করলে লোকাল Flan-T5 ব্রেইন মেমোরি ও লেসন বিশ্লেষণ করে কাজ চালাবে (Cross-Model Fallback)
    if llm_brain:
        try:
            # লোকাল মডেল ছোট হওয়ায় সংক্ষিপ্ত ও কার্যকরি প্রম্পট পাঠানো হচ্ছে
            short_prompt = f"Command: {query}. Rule: {agent_memory.get('lessons_learned', ['Be safe'])[0]}"
            res_llm = llm_brain(short_prompt, max_length=60, do_sample=False)
            if res_llm and len(res_llm) > 0:
                return res_llm[0].get("generated_text", ""), "🟡 Local AI Brain (Memory-Infused Fallback)"
        except:
            pass
            
    # ৩. শেষ বিকল্প হিসেবে রুল বেসড ফলব্যাক
    return "Optimized via universal memory lessons and internal logic.", "🔵 Internal Rule-based Fallback"


# ==========================================================
# --- 🛠️ CORE SYSTEM TOOLS & TRADING MODULES ---
# ==========================================================

def get_live_solana_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&include_24hr_change=true"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            price = data.get("solana", {}).get("usd", 0)
            change = data.get("solana", {}).get("usd_24h_change", 0)
            return True, price, change
    except Exception as e:
        print(f"Market Tool Error: {e}")
    return False, 0.0, 0.0

def tool_check_crypto_fear_greed(*args, **kwargs):
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            item = data.get("data", [])[0]
            val = item.get("value")
            sentiment = item.get("value_classification")
            return True, f"Crypto Market Sentiment: {val}/100 ({sentiment})"
    except Exception as e:
        print(f"Fear & Greed Error: {e}")
    return False, "Fear & Greed index fetch failed."

def tool_online_crypto_news_sentiment(*args, **kwargs):
    try:
        url = "https://api.coingecko.com/api/v3/news"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            articles = data.get("data", [])[:4]
            if not articles:
                return False, "No public news articles retrieved."
            
            headlines = [art.get("title") for art in articles if art.get("title")]
            bullish_keywords = ["surge", "rally", "gain", "bull", "high", "growth", "approve", "launch", "pump", "adoption"]
            bearish_keywords = ["crash", "drop", "fall", "bear", "down", "hack", "ban", "loss", "dump", "risk"]
            
            score = 0
            combined_text = " ".join(headlines).lower()
            for word in bullish_keywords:
                if word in combined_text:
                    score += 1
            for word in bearish_keywords:
                if word in combined_text:
                    score -= 1
            
            sentiment_label = "🟢 Bullish / Positive" if score >= 0 else "🔴 Cautious / Bearish"
            news_list_str = "\n".join([f"• {h}" for h in headlines[:3]])
            return True, f"📰 *Web News Analysis:*\n{news_list_str}\n\n*Signal:* `{sentiment_label}` (Score: {score})"
    except Exception as e:
        print(f"News Analysis Error: {e}")
    return False, "Failed to analyze online crypto news."

def tool_system_full_access_controller(query: str = "status", *args, **kwargs):
    try:
        folder = "system_logs"
        os.makedirs(folder, exist_ok=True)
        filename = f"{folder}/system_access_activity.log"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"[{time.ctime()}] System Full Access Executed for Query: {query}\n")
        return True, f"System API & Core Modules successfully accessed and verified for task: '{query}'"
    except Exception as e:
        return False, f"System Access Error: {str(e)}"

def dispatch_to_real_trading_system(action: str, amount_usd: float):
    global agent_memory
    endpoint = agent_memory.get("real_system_endpoint")
    api_key = agent_memory.get("real_system_api_key")
    
    payload = {"action": action, "amount_usd": amount_usd, "source": "AI_Brain_Ultimate", "timestamp": time.time()}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        res = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return True, f"🚀 [Real Body Dispatch Success] Action '{action}' executed. Response: {res.text}"
        else:
            return False, f"⚠️ [Real Body Error] Status {res.status_code}: {res.text}"
    except Exception as e:
        return False, f"🔴 [Real Body Connection Failed]: {str(e)}"

def tool_simulated_crypto_trader(action: str = "BUY", amount_usd: float = 100.0, *args, **kwargs):
    global agent_memory
    success, current_price, change_24h = get_live_solana_price()
    if not success or current_price == 0:
        return False, "Failed to fetch live market price."

    mode = agent_memory.get("mode", "virtual")
    action = action.upper()

    if mode == "real":
        wallet = agent_memory["wallet"]
        if wallet["total_trades"] < 3:
            return False, "🛡️ [Confidence Gate Block]: Real trade rejected. Minimum 3 virtual trades required first."
        return dispatch_to_real_trading_system(action, amount_usd)

    wallet = agent_memory["wallet"]
    with memory_lock:
        if action == "BUY":
            if wallet["balance_usd"] >= amount_usd:
                crypto_amount = amount_usd / current_price
                wallet["balance_usd"] -= amount_usd
                wallet["crypto_holding"] += crypto_amount
                wallet["total_trades"] += 1
                wallet["successful_trades"] += 1
                wallet["trade_history"].append({"time": time.ctime(), "action": "BUY", "price": current_price, "amount_usd": amount_usd, "crypto": crypto_amount})
                save_agent_memory(agent_memory)
                return True, f"🟢 [Virtual Sandbox BUY] Purchased {crypto_amount:.4f} SOL at ${current_price} \vert{} Spent:${amount_usd}"
            else:
                return False, "🔴 [Sandbox Error] Insufficient virtual USD balance."

        elif action == "SELL":
            if wallet["crypto_holding"] > 0:
                sold_crypto = wallet["crypto_holding"]
                sold_value = sold_crypto * current_price
                invested_est = sold_value / (1 + (change_24h / 100))
                profit_loss = sold_value - invested_est
                wallet["balance_usd"] += sold_value
                wallet["crypto_holding"] = 0.0
                wallet["total_trades"] += 1
                if profit_loss >= 0:
                    wallet["successful_trades"] += 1
                else:
                    wallet["failed_trades"] += 1
                wallet["trade_history"].append({"time": time.ctime(), "action": "SELL", "price": current_price, "sold_value": sold_value, "pnl": profit_loss})
                save_agent_memory(agent_memory)
                return True, f"🔵 [Virtual Sandbox SELL] Sold {sold_crypto:.4f} SOL at ${current_price} \vert{} PnL:${profit_loss:.2f}"
            else:
                return False, "🔴 [Sandbox Error] No active crypto holdings to sell."
    return False, "Invalid simulation action."


AVAILABLE_TOOLS = {
    "Market_Price_Checker": lambda *a, **kw: get_live_solana_price(),
    "Simulated_Crypto_Trader": tool_simulated_crypto_trader,
    "Real_System_Dispatcher": dispatch_to_real_trading_system,
    "System_API_Access_Module": tool_system_full_access_controller,
    "Crypto_Fear_Greed_Index": tool_check_crypto_fear_greed,
    "Crypto_News_Sentiment_Analyzer": tool_online_crypto_news_sentiment
}


# ==========================================================
# --- 🤖 AGENTIC EXECUTION & UNIFIED AI BRAIN ---
# ==========================================================

def record_ai_feedback(strategy_name: str, success: bool):
    global agent_memory
    try:
        with memory_lock:
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

def run_ai_analysis_and_execute(query: str) -> str:
    global agent_memory
    cleaned_query = query.lower().strip()
    current_mode = agent_memory.get("mode", "virtual").upper()

    try:
        # ইউনিভার্সাল মেমোরি প্রম্পট জেনারেট করে যেকোনো এআই ইঞ্জিনের কাছে পাঠানো হচ্ছে
        ai_thought, ai_source = ask_ai_with_universal_fallback(cleaned_query)

        if "buy" in cleaned_query or "purchase" in cleaned_query:
            success, msg = tool_simulated_crypto_trader(action="BUY", amount_usd=150.0)
            record_ai_feedback("Simulated_Crypto_Trader", success)
        elif "sell" in cleaned_query:
            success, msg = tool_simulated_crypto_trader(action="SELL")
            record_ai_feedback("Simulated_Crypto_Trader", success)
        elif "news" in cleaned_query or "sentiment" in cleaned_query:
            success, msg = tool_online_crypto_news_sentiment()
            record_ai_feedback("Crypto_News_Sentiment_Analyzer", success)
        else:
            success, msg = tool_system_full_access_controller(query=query)
            record_ai_feedback("System_API_Access_Module", success)

        wallet = agent_memory["wallet"]
        _, current_price, _ = get_live_solana_price()
        total_val = wallet["balance_usd"] + (wallet["crypto_holding"] * current_price)

        return (
            f"🧠 *AI Brain Autonomous Execution*\n"
            f"⚙️ *Active Mode:* `{current_mode}`\n"
            f"⚡ *AI Engine:* `{ai_source}`\n"
            f"📌 *Command:* `{query}`\n"
            f"💡 *Brain Thought (Universal Memory Infused):* `{ai_thought}`\n\n"
            f"🛠️ *Execution Result:*\n{msg}\n\n"
            f"📊 *Portfolio & Status Overview:*\n"
            f"• Cash/Balance: `${wallet['balance_usd']:.2f}`\n"
            f"• Holdings: `{wallet['crypto_holding']:.4f} SOL`\n"
            f"• Net Worth: `${total_val:.2f}`\n"
            f"• Success/Fail: `✅ {wallet['successful_trades']} | ❌ {wallet['failed_trades']}`"
        )
    except Exception as e:
        return f"💡 [Agent Execution Error]: {str(e)}"


# --- টেলিগ্রাম বট ব্যাকগ্রাউন্ড ওয়ার্কার ---
def telegram_bot_worker():
    global agent_memory
    time.sleep(10)
    offset = 0
    print("Ultimate Autonomous Crypto Agent Telegram Bot Started 🤖")
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
                    
                    if text.startswith("/addkey "):
                        new_key = text.replace("/addkey ", "").strip()
                        is_valid, reason = validate_and_test_gemini_key(new_key)
                        if is_valid:
                            with memory_lock:
                                if "gemini_keys" not in agent_memory:
                                    agent_memory["gemini_keys"] = []
                                if new_key not in agent_memory["gemini_keys"]:
                                    agent_memory["gemini_keys"].append(new_key)
                                save_agent_memory(agent_memory)
                            reply_text = f"✅ *Gemini API Key Added Successfully!* Total active keys: `{len(agent_memory['gemini_keys'])}`"
                        else:
                            reply_text = f"❌ *Invalid API Key Rejected!*\nReason: `{reason}`"
                            
                    elif text == "/keys":
                        keys = agent_memory.get("gemini_keys", [])
                        reply_text = f"🔑 *Saved Gemini API Keys Count:* `{len(keys)}`\nSystem is configured to rotate and fallback automatically."
                        
                    elif text == "/start":
                        reply_text = "🤖 *Ultimate Autonomous Crypto Brain with Universal Memory Sharing Active!*"
                    elif text == "/wallet":
                        wallet = agent_memory["wallet"]
                        success, price, change = get_live_solana_price()
                        total_val = wallet["balance_usd"] + (wallet["crypto_holding"] * price)
                        mode = agent_memory.get("mode", "virtual")
                        reply_text = (
                            f"💼 *System Status & Portfolio:*\n\n"
                            f"• Current Operating Mode: `⚡ {mode.upper()}`\n"
                            f"• Live Solana Price: `${price} USD` ({change:.2f}%)\n"
                            f"• Cash USD: `${wallet['balance_usd']:.2f}`\n"
                            f"• Crypto Holding: `{wallet['crypto_holding']:.4f} SOL`\n"
                            f"• Total Net Worth: `${total_val:.2f}`\n"
                            f"• Success/Fail: `✅ {wallet['successful_trades']} | ❌ {wallet['failed_trades']}`"
                        )
                    elif text == "/news" or text == "/sentiment":
                        success, news_msg = tool_online_crypto_news_sentiment()
                        record_ai_feedback("Crypto_News_Sentiment_Analyzer", success)
                        reply_text = news_msg
                    elif text == "/modevirtual":
                        with memory_lock:
                            agent_memory["mode"] = "virtual"
                            save_agent_memory(agent_memory)
                        reply_text = "🔄 *Switched to Virtual Sandbox Mode!*"
                    elif text == "/modereal":
                        with memory_lock:
                            agent_memory["mode"] = "real"
                            save_agent_memory(agent_memory)
                        reply_text = "⚠️ *Switched to REAL Production Mode!*"
                    elif text == "/stats":
                        metrics = agent_memory.get("tool_metrics", {})
                        stats_lines = [f"• *{k}* ✅ {v['success']} | ❌ {v['fail']}" for k, v in metrics.items()]
                        reply_text = "📊 *System Tool Performance Metrics:*\n\n" + "\n".join(stats_lines)
                    elif text == "/tools":
                        reply_text = "🛠️ *Active System Modules & Tools:*\n" + "\n".join([f"• {t}" for t in AVAILABLE_TOOLS.keys()])
                    elif text == "/lessons":
                        lessons = agent_memory.get("lessons_learned", [])
                        reply_text = "🧠 *AI Learned Rules & Lessons:*\n" + "\n".join([f"• {l}" for l in lessons])
                    elif text == "/resetwallet":
                        with memory_lock:
                            agent_memory["wallet"] = default_memory_data["wallet"]
                            save_agent_memory(agent_memory)
                        reply_text = "🧹 Simulation wallet reset to $1000 virtual balance!"
                    else:
                        reply_text = run_ai_analysis_and_execute(text)
                    
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"})
                    
        except Exception as e:
            print(f"Telegram Bot Error: {e}")
            time.sleep(5)

@app.on_event("startup")
def startup_event():
    threading.Thread(target=telegram_bot_worker, daemon=True).start()
    print("Autonomous Brain Threads Initialized 🚀")

@app.get("/")
def home():
    mode = agent_memory.get("mode", "virtual")
    keys_count = len(agent_memory.get("gemini_keys", []))
    return {"status": "Ultimate Autonomous Crypto Brain is Live 🟢", "mode": mode, "gemini_keys_registered": keys_count, "version": "24.0"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
