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

app = FastAPI(title="Smart AI Data Analyst & Autonomous API", version="6.0")

# টেলিগ্রাম কনফিগারেশন
TELEGRAM_BOT_TOKEN = "8974206752:AAFqOusGoMFjh0snVhUQZFEvt58jJ56FVIk"
ADMIN_TELEGRAM_ID = 7363218232

# ভ্যালিড এপিআই কি-গুলোর তালিকা
VALID_API_KEYS = {
    os.getenv("MY_CUSTOM_API_KEY", "my-secret-solana-ai-key-12345")
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
def run_ai_analysis(chat_id: int, query: str) -> str:
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
        
        structured_prompt = (
            f"Previous Context:\n{history_text}\n\n"
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
        # সেলফ রিকভারি ফলব্যাক রেসপন্স
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
                            json={"chat_id": chat_id, "text": "Access Denied - অথরাইজড নয়।"}
                        )
                        continue
                    
                    if text == "/generatekey":
                        new_key = f"ai_key_{secrets.token_hex(12)}"
                        VALID_API_KEYS.add(new_key)
                        reply_text = f"🔑 নতুন এপিআই কি জেনারেট করা হয়েছে:\n\n`{new_key}`\n\nএটি অন্য সিস্টেমে ব্যবহার করতে পারবেন।"
                    
                    elif text in ["/start", "/help"]:
                        reply_text = (
                            "🤖 **অটোনোমাস এআই বট উইথ মেমোরি ও সেলফ-রিকভারি সক্রিয়!**\n\n"
                            "📌 `/generatekey` - নতুন এপিআই কি তৈরি করতে\n"
                            "📌 যেকোনো প্রশ্ন পাঠান - মেমোরি ও লাইভ সার্চসহ এআই বিশ্লেষণ পেতে।"
                        )
                    
                    elif text == "/clearmemory":
                        CHAT_HISTORIES[chat_id] = []
                        reply_text = "🧹 মেমোরি সফলভাবে পরিষ্কার করা হয়েছে!"
                    
                    else:
                        # প্রসেসিং মেসেজ পাঠানো
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
            # সেলফ রিকভারি লজিক: ইন্টারনেট বা টেলিগ্রাম এপিআই ডাউন হলে ক্র্যাশ না করে ৫ সেকেন্ড পর রিকভার করবে
            print(f"Telegram Bot Self-Recovery Triggered due to: {e}")
            time.sleep(5)


@app.on_event("startup")
def startup_event():
    bot_thread = threading.Thread(target=telegram_bot_worker, daemon=True)
    bot_thread.start()
    print("Autonomous Background Threads Initialized 🚀")


class DataAnalysisRequest(BaseModel):
    query: str
    max_length: int = 150

def verify_api_key(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    if token not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return token

@app.get("/")
def home():
    return {"status": "Autonomous AI Analyst Engine with Memory & Self-Recovery is Active 🟢"}

@app.post("/api/v1/smart-analyze")
def smart_analyze_and_decide(data: DataAnalysisRequest, token: str = Depends(verify_api_key)):
    try:
        # এক্সটার্নাল এপিআই রিকোয়েস্টের জন্যও সেলফ-রিকভারিং এনালাইসিস
        result = run_ai_analysis(0, data.query)
        return {
            "status": "success",
            "engine": "Autonomous AI with Memory & Self-Recovery",
            "user_query": data.query,
            "ai_decision_and_analysis": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Self-Recovery Triggered Error: {str(e)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
