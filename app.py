from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from transformers import pipeline
from duckduckgo_search import DDGS
import threading
import time
import requests
import secrets
import os

app = FastAPI(title="Smart AI Data Analyst API with Telegram Bot", version="5.0")

# টেলিগ্রাম কনফিগারেশন
TELEGRAM_BOT_TOKEN = "8974206752:AAFqOusGoMFjh0snVhUQZFEvt58jJ56FVIk"
ADMIN_TELEGRAM_ID = 7363218232

# ভ্যালিড এপিআই কি-গুলোর তালিকা (বট থেকে নতুন কি জেনারেট করলে এখানে জমা হবে)
VALID_API_KEYS = {
    os.getenv("MY_CUSTOM_API_KEY", "my-secret-solana-ai-key-12345")
}

# Hugging Face থেকে হালকা মডেল লোড করা
print("Loading AI LLM Brain...")
llm_brain = pipeline("text2text-generation", model="google/flan-t5-small") 
print("LLM Brain Loaded Successfully!")


# --- এআই এনালাইসিস লজিক ফাংশন ---
def run_ai_analysis(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=2)]
            
        if not results:
            return "কোনো অনলাইন ডাটা পাওয়া যায়নি।"
        
        combined_data = ""
        for i, res in enumerate(results):
            combined_data += f"Source {i+1}: {res.get('title', '')} - {res.get('body', '')}\n"
        
        structured_prompt = (
            f"Analyze the following online data and provide a clear business decision or conclusion.\n\n"
            f"User Question: {query}\n\n"
            f"Fetched Online Data:\n{combined_data}\n\n"
            f"Analysis and Decision:"
        )
        
        ai_output = llm_brain(structured_prompt, max_length=150, do_sample=True)
        return ai_output[0]['generated_text']
    except Exception as e:
        return f"Processing Error: {str(e)}"


# --- টেলিগ্রাম বট লং-পোলিং ব্যাকগ্রাউন্ড ওয়ার্কার ---
def telegram_bot_worker():
    """
    ব্যাকগ্রাউন্ডে টেলিগ্রামের মেসেজ চেক করবে এবং কমান্ড হ্যান্ডেল করবে।
    """
    time.sleep(10) # সার্ভার পুরোপুরি চালু হওয়ার জন্য অপেক্ষা
    offset = 0
    print("Telegram Bot Background Worker Started 🤖")
    
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
                    
                    # শুধুমাত্র নির্দিষ্ট অ্যাডমিন আইডি (7363218232) এর মেসেজ প্রসেস করবে
                    if user_id != ADMIN_TELEGRAM_ID:
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                            json={"chat_id": chat_id, "text": "Access Denied - আপনি এই বটের অনুমতিপ্রাপ্ত ব্যবহারকারী নন।"}
                        )
                        continue
                    
                    # কমান্ড ১: /generatekey (নতুন এপিআই কি জেনারেট করবে)
                    if text == "/generatekey":
                        new_key = f"ai_key_{secrets.token_hex(12)}"
                        VALID_API_KEYS.add(new_key)
                        reply_text = (
                            f"🔑 নতুন এপিআই কি সফলভাবে জেনারেট করা হয়েছে!\n\n"
                            f"`{new_key}`\n\n"
                            f"এই কি শুধুমাত্র আপনার সিস্টেমে কাজ করবে।"
                        )
                    
                    # কমান্ড ২: /start বা /help
                    elif text in ["/start", "/help"]:
                        reply_text = (
                            "স্বাগতম! আপনার স্মার্ট এআই ডাটা অ্যানালিস্ট বডি সক্রিয় রয়েছে।\n\n"
                            "📌 **কমান্ডসমূহ:**\n"
                            "👉 `/generatekey` - নতুন সিক্রেট এপিআই কি তৈরি করতে\n"
                            "👉 যেকোনো প্রশ্ন বা বিষয় লিখে পাঠান - সরাসরি এআই এনালাইসিস ও সিদ্ধান্ত পেতে।"
                        )
                    
                    # সাধারণ টেক্সট বা কুয়েরি পাঠালে সরাসরি এআই এনালাইসিস করে জবাব দেবে
                    else:
                        reply_text = f"🔄 এনালাইসিস করা হচ্ছে...\n\nप्रश्न: {text}\n\n"
                        # প্রথমে একটি প্রসেসিং মেসেজ পাঠানো
                        res_msg = requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                            json={"chat_id": chat_id, "text": reply_text}
                        ).json()
                        
                        # এআই এনালাইসিস রান করা
                        ai_result = run_ai_analysis(text)
                        
                        # আগের মেসেজটি আপডেট বা নতুন করে ফলাফল পাঠানো
                        reply_text = f"💡 **এআই সিদ্ধান্ত ও বিশ্লেষণ:**\n\n{ai_result}"
                        if res_msg.get("ok"):
                            msg_id = res_msg["result"]["message_id"]
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText",
                                json={"chat_id": chat_id, "message_id": msg_id, "text": reply_text}
                            )
                        continue
                    
                    # সাধারণ রেসপন্স পাঠানোর জন্য
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"}
                    )
                    
        except Exception as e:
            print(f"Telegram Bot Error: {e}")
            time.sleep(5)


# FastAPI স্টার্ট হওয়ার সাথে সাথে টেলিগ্রাম বট থ্রেড চালু হবে
@app.on_event("startup")
def startup_event():
    bot_thread = threading.Thread(target=telegram_bot_worker, daemon=True)
    bot_thread.start()
    print("Telegram Bot Thread Initiated Successfully 🚀")


class DataAnalysisRequest(BaseModel):
    query: str
    max_length: int = 150

def verify_api_key(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    if token not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key - অ্যাক্সেস ডিনাইড")
    return token

@app.get("/")
def home():
    return {"status": "Smart AI Data Analyst & Telegram Bot Engine is Active 🟢"}

@app.post("/api/v1/smart-analyze")
def smart_analyze_and_decide(data: DataAnalysisRequest, token: str = Depends(verify_api_key)):
    user_query = data.query
    
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(user_query, max_results=2)]
            
        combined_data = ""
        for i, res in enumerate(results):
            combined_data += f"Source {i+1}: {res.get('title', '')} - {res.get('body', '')}\n"
            
        structured_prompt = (
            f"Analyze the following online data and provide a clear business decision or conclusion.\n\n"
            f"User Question: {user_query}\n\n"
            f"Fetched Online Data:\n{combined_data}\n\n"
            f"Analysis and Decision:"
        )
        
        ai_output = llm_brain(structured_prompt, max_length=data.max_length, do_sample=True)
        generated_text = ai_output[0]['generated_text']
        
        return {
            "status": "success",
            "engine": "Smart AI Data Analyst Engine with Telegram Bot",
            "user_query": user_query,
            "ai_decision_and_analysis": generated_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis & Processing Error: {str(e)}")