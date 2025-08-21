from fastapi import FastAPI, Request, HTTPException
import psycopg2
import json
import re
from datetime import datetime
import os

app = FastAPI()

DB_URL = os.getenv("DB_URL")

def insert_notification(data: dict):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Parse timestamp
    raw_time = data.get("notification_time")
    notification_time = None
    if raw_time:
        try:
            notification_time = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            notification_time = None

    # Ensure messages is JSON
    messages = data.get("messages")
    if isinstance(messages, str):
        messages = json.dumps({"text": messages})

    query = """
    INSERT INTO callgear_notifications (
        notification_time,
        chat_id,
        visitor_phone_number,
        messages,
        employee_full_name,
        visitor_name,
        visitor_id,
        status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    cur.execute(query, (
        notification_time,
        data.get("chat_id"),
        data.get("visitor_phone_number"),
        messages,
        data.get("employee_full_name"),
        data.get("visitor_info", {}).get("visitor_name"),
        data.get("visitor_info", {}).get("visitor_id"),
        data.get("status", "Open")
    ))

    conn.commit()
    cur.close()
    conn.close()

@app.post("/webhook")
async def webhook(request: Request):
    raw_body = await request.body()
    body_text = raw_body.decode("utf-8")
    print("Original payload:", body_text)

    cleaned_text = re.sub(r'""(.*?)""', r'"\1"', body_text)
    print("Cleaned payload:", cleaned_text)

    try:
        data = json.loads(cleaned_text)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse JSON: {str(e)}")

    try:
        insert_notification(data)
        return {"status": "success"}

    except Exception as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



@app.get("/")
def read_root():
    return {"message": "Webhook, V1.1.0"}


if __name__ == "__main__":# or Run using: uvicorn cg-webhook:app --host 0.0.0.0 --port 8005 --reload
    import uvicorn
    uvicorn.run("cg-webhook:app", host="0.0.0.0", port=8005, reload=True)# dev
    #uvicorn.run(app, host="0.0.0.0", port=8005)# prod
