from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from transformers import pipeline
from duckduckgo_search import DDGS
import threading
import time
import requests
import secrets
import os
import uvicorn

app = FastAPI(title="Optimized Autonomous AI API for Render Free Tier", version="8.5")

# টেলিগ্রাম কনফিগারেশন
TELEGRAM_BOT_TOKEN = "8931678358:AAEFHNA__FVJlwB6LGbkYRFPXVMm7fYBaaA"
ADMIN_TELEGRAM_ID = 7363218232

# আপনার রেন্ডার ওয়েব সার্ভারের পাবলিক লিঙ্ক (অ্যান্টি-স্লিপ পিংয়ের জন্য আপনার এপিআই লিংক এখানে দিন)
RENDER_APP_URL = "https://ai-api-cgzb.onrender.com"

# ভ্যালিড এপিআই কি-গুলোর তালিকা
VALID_API_KEYS = {
    os.getenv("MY_CUSTOM_API_KEY", "my-secret-solana-ai-key-12345"),
    "ai_key_1762b5a10bdc7ed4a5db091d"  # আপনার জেনারেট করা নির্দিষ্ট এপিআই কি
}

# চ্যাট মেমোরি স্টোর করার জন্য ডিকশনারি
CHAT_HISTORIES = {}

# Hugging Face থেকে হালকা মডেল লোড করা (সেলফ-রিকভারি ট্রাই-캐চ সহ)
print("Loading AI LLM Brain...")
try:
    llm_brain = pipeline("text2text-generation", model="google/flan-t5-small")
    print("LLM Brain Loaded Successfully!")
except Exception as e:
    print(f"Model Load Warning: {e}")
    llm_brain = None


# --- সেলফ-রিকভারিং ও অপ্টিমাইজড এআই অ্যানালিসিস লজিক ---
def run_ai_analysis(chat_id: int, query: str, balance: float = 0.0, mission: str = "") -> str:
    try:
        # ইন্টারনেট সার্চ উইথ সেলফ রিকভারি/ফলব্যাক
        search_results = []
        try:
            with DDGS() as ddgs:
                search_results = [r for r in ddgs.text(query, max_results=2)]
        except Exception as search_err:
            print(f"Search warning (Self-recovered): {search_err}")
        
        combined_data = ""
        if search_results:
            for i, res in enumerate(search_results):
                combined_data += f"Source {i+1}: {res.get('title', '')} - {res.get('body', '')}\n"
        else:
            combined_data = "Solana network trending signals, low gas fee optimization, and smart automated micro-profit strategy."
        
        # ব্যালেন্স এবং মিশন থাকলে তা যুক্ত করা
        extra_context = ""
        if balance == 0.0:
            extra_context += "Wallet Status: 0.0 SOL (Zero Balance). Focus on off-chain signal hunting, free airdrops, and gas-saving strategies.\n"
        else:
            extra_context += f"Account/Wallet Balance: {balance} SOL\n"
            
        if mission:
            extra_context += f"Specific Mission: {mission}\n"
        
        structured_prompt = (
            f"{extra_context}"
            f"Provide a clear, actionable crypto/business decision or strategy.\n"
            f"Objective: {query}\n"
            f"Market Context:\n{combined_data[:300]}\n"
            f"Decision:"
        )
        
        if llm_brain:
            ai_output = llm_brain(structured_prompt, max_length=120, do_sample=False)
            answer = ai_output[0]['generated_text']
        else:
            answer = f"💡 [Resilient AI Plan]: বর্তমান মার্কেট ও জিরো ব্যালেন্স অনুযায়ী পরামর্শ হলো—সোলানার গ্যাস ফি বাঁচিয়ে অফ-চেইন ট্রেন্ডিং টোকেন ও ফ্রি টেস্টনেট স্ক্যান করুন।"
            
        return answer
    except Exception as e:
        return f"💡 [Resilient Fallback Active]: বর্তমান নেটওয়ার্ক ট্রাফিক বেশি থাকায় ফলব্যাক স্ট্র্যাটেজি ব্যবহার করা হয়েছে। সোলানা অটোমেশন ও সিগন্যাল হান্টিং চালিয়ে যান। (Error: {str(e)[:30]})"


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
        # প্রতি ৮ মিনিট পর পর রিকোয়েস্ট পাঠাবে (রেন্ডারের ১৫ মিনিটের লিমিটের আগেই)
        time.sleep(480)


# --- সেলফ-রিকভারিং টেলিগ্রাম বট ব্যাকগ্রাউন্ড ওয়ার্কার ---
def telegram_bot_worker():
    time.sleep(15)
    offset = 0
    print("Autonomous Telegram Bot Worker Started 🤖")
    
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
                            json={"chat_id": chat_id, "text": "Access Denied - আপনি এই বটের অনুমতিপ্রাপ্ত ব্যবহারকারী নন।"}
                        )
                        continue
                    
                    if text == "/generatekey":
                        new_key = f"ai_key_{secrets.token_hex(12)}"
                        VALID_API_KEYS.add(new_key)
                        reply_text = f"🔑 নতুন এপিআই কি জেনারেট করা হয়েছে:\n\n`{new_key}`\n\nএটি আপনার অন্য সিস্টেমে ব্যবহার করতে পারবেন।"
                    
                    elif text in ["/start", "/help"]:
                        reply_text = (
                            "🤖 **স্মার্ট এআই ডাটা অ্যানালিস্ট ও অটোনমাস বট সক্রিয়!**\n\n"
                            "📌 `/generatekey` - নতুন সিক্রেট এপিআই কি তৈরি করতে\n"
                            "📌 `/clearmemory` - চ্যাট মেমোরি পরিষ্কার করতে\n"
                            "📌 যেকোনো প্রশ্ন বা বিষয় লিখে পাঠান - সরাসরি লাইভ সার্চ ও এআই এনালাইসিস পেতে।"
                        )
                    
                    elif text == "/clearmemory":
                        CHAT_HISTORIES[chat_id] = []
                        reply_text = "🧹 মেমোরি সফলভাবে পরিষ্কার করা হয়েছে!"
                    
                    else:
                        res_msg = requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                            json={"chat_id": chat_id, "text": "🔄 মেমোরি ও সার্চ চেক করে এনালাইসিস করা হচ্ছে..."}
                        ).json()
                        
                        ai_result = run_ai_analysis(chat_id, text)
                        
                        reply_text = f"💡 **এআই বিশ্লেষণ ও সিদ্ধান্ত:**\n\n{ai_result}"
                        if res_msg.get("ok"):
                            msg_id = res_msg["result"]["message_id"]
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText",
                                json={"chat_id": chat_id, "message_id": msg_id, "text": reply_text}
                            )
                        continue
                    
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"}
                    )
                    
        except Exception as e:
            print(f"Telegram Bot Self-Recovery Triggered due to: {e}")
            time.sleep(5)


@app.on_event("startup")
def startup_event():
    # টেলিগ্রাম বট এবং অ্যান্টি-স্লিপ থ্রেড চালু করা
    bot_thread = threading.Thread(target=telegram_bot_worker, daemon=True)
    bot_thread.start()
    
    ping_thread = threading.Thread(target=self_ping_worker, daemon=True)
    ping_thread.start()
    print("Autonomous Background & Anti-Sleep Threads Initialized 🚀")


# 👉 অপ্টিমাইজড ও ফ্লেক্সিবল রিকোয়েস্ট মডেল (যাতে বট থেকে ডেটা মিসিং হলেও ক্র্যাশ না করে)
class DataAnalysisRequest(BaseModel):
    query: Optional[str] = "Analyze Solana market trend and give automated micro-profit strategy."
    balance: float = 0.0
    mission: Optional[str] = "Solana autonomous crypto earning and signal hunting"
    max_length: int = 150

def verify_api_key(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    if token not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key - অ্যাক্সেস ডিনাইড")
    return token

@app.get("/")
def home():
    return {"status": "Smart AI Data Analyst & Autonomous API Engine (Optimized for Render Free Tier) is Active 🟢"}

@app.post("/api/v1/smart-analyze")
def smart_analyze_and_decide(data: DataAnalysisRequest, token: str = Depends(verify_api_key)):
    try:
        # রিকোয়েস্ট থেকে প্রাপ্ত query, balance এবং mission এআই অ্যানালিসিস ফাংশনে পাস করা হলো
        result = run_ai_analysis(0, data.query or "Solana strategy", data.balance, data.mission or "")
        return {
            "status": "success",
            "engine": "Autonomous AI with Anti-Sleep & Self-Recovery",
            "user_query": data.query,
            "balance_passed": data.balance,
            "mission_passed": data.mission,
            "strategy_advice": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Self-Recovery Triggered Error: {str(e)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
