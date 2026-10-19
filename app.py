from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from transformers import pipeline
from duckduckgo_search import DDGS
import threading
import time
import requests
import secrets
import os
import uvicorn

app = FastAPI(title="Smart AI Data Analyst & Autonomous API", version="8.2")

# টেলিগ্রাম কনফিগারেশন
TELEGRAM_BOT_TOKEN = "8931678358:AAEFHNA__FVJlwB6LGbkYRFPXVMm7fYBaaA"
ADMIN_TELEGRAM_ID = 7363218232

# ভ্যালিড এপিআই কি-গুলোর তালিকা
VALID_API_KEYS = {
    os.getenv("MY_CUSTOM_API_KEY", "my-secret-solana-ai-key-12345"),
    "ai_key_1762b5a10bdc7ed4a5db091d"  # আপনার জেনারেট করা নির্দিষ্ট এপিআই কি
}

# চ্যাট মেমোরি স্টোর করার জন্য ডিকশনারি (Short-term Memory)
CHAT_HISTORIES = {}

# Hugging Face থেকে হালকা মডেল লোড করা (সেলফ-রিকভারি ট্রাই-ক্যাচ সহ)
print("Loading AI LLM Brain...")
try:
    llm_brain = pipeline("text2text-generation", model="google/flan-t5-small")
    print("LLM Brain Loaded Successfully!")
except Exception as e:
    print(f"Model Load Warning: {e}")
    llm_brain = None


# --- সেলফ-রিকভারিং এআই অ্যানালিসিস লজিক ---
def run_ai_analysis(chat_id: int, query: str, balance: float = 0.0, mission: str = "") -> str:
    try:
        # মেমোরি থেকে পূর্বের ইতিহাস যুক্ত করা
        history = CHAT_HISTORIES.get(chat_id, [])
        history_text = "\n".join([f"Q: {h['q']}\nA: {h['a']}" for h in history[-2:]]) # শেষ ২ টি চ্যাট মনে রাখবে
        
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
            combined_data = "No live web data found, using internal reasoning."
        
        # ব্যালেন্স এবং মিশন থাকলে তা প্রম্পটের সাথে যুক্ত করা
        extra_context = ""
        if balance > 0.0:
            extra_context += f"Account/Wallet Balance: {balance}\n"
        if mission:
            extra_context += f"Specific Mission/Objective: {mission}\n"
        
        structured_prompt = (
            f"Previous Context:\n{history_text}\n\n"
            f"{extra_context}"
            f"Analyze the data and provide a clear business decision or conclusion.\n"
            f"Question: {query}\n"
            f"Data:\n{combined_data}\n"
            f"Decision:"
        )
        
        if llm_brain:
            ai_output = llm_brain(structured_prompt, max_length=150, do_sample=True)
            answer = ai_output[0]['generated_text']
        else:
            answer = f"AI model is currently reloading. Based on web data: {combined_data[:100]}"
            
        # মেমোরিতে নতুন চ্যাট সেভ করা (Memory Update)
        if chat_id not in CHAT_HISTORIES:
            CHAT_HISTORIES[chat_id] = []
        CHAT_HISTORIES[chat_id].append({"q": query, "a": answer})
        
        return answer
    except Exception as e:
        return f"System Auto-Recovered from minor error. Analysis fallback: Unable to fully process due to [{str(e)}], but your system is safe and running."


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
    bot_thread = threading.Thread(target=telegram_bot_worker, daemon=True)
    bot_thread.start()
    print("Autonomous Background Threads Initialized 🚀")


# 👉 ব্যালেন্স এবং মিশন ফিল্ডসহ আপডেট করা রিকোয়েস্ট মডেল
class DataAnalysisRequest(BaseModel):
    query: str
    balance: float = 0.0
    mission: str = ""
    max_length: int = 150

def verify_api_key(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    if token not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key - অ্যাক্সেস ডিনাইড")
    return token

@app.get("/")
def home():
    return {"status": "Smart AI Data Analyst & Autonomous API Engine with Memory & Self-Recovery is Active 🟢"}

@app.post("/api/v1/smart-analyze")
def smart_analyze_and_decide(data: DataAnalysisRequest, token: str = Depends(verify_api_key)):
    try:
        # রিকোয়েস্ট থেকে প্রাপ্ত query, balance এবং mission এআই অ্যানালিসিস ফাংশনে পাস করা হলো
        result = run_ai_analysis(0, data.query, data.balance, data.mission)
        return {
            "status": "success",
            "engine": "Autonomous AI with Memory & Self-Recovery",
            "user_query": data.query,
            "balance_passed": data.balance,
            "mission_passed": data.mission,
            "ai_decision_and_analysis": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Self-Recovery Triggered Error: {str(e)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
