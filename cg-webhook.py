from fastapi import FastAPI, Request, HTTPException
import psycopg2
import json
import os

app = FastAPI()

DB_URL = os.getenv("DB_URL")

def insert_notification(data: dict):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

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
        data.get("notification_time"),
        data.get("chat_id"),
        data.get("visitor_phone_number"),
        json.dumps(data.get("messages")) if isinstance(data.get("messages"), (dict, list)) else data.get("messages"),
        data.get("employee_full_name"),
        data.get("visitor_info", {}).get("visitor_name") if data.get("visitor_info") else None,
        data.get("visitor_info", {}).get("visitor_id") if data.get("visitor_info") else None,
        data.get("status", "Open")
    ))

    conn.commit()
    cur.close()
    conn.close()


@app.post("/webhook")
async def webhook(request: Request):
    try:
        raw_body = await request.body()
        data = json.loads(raw_body.decode("utf-8"))  # Force JSON parsing
        print(data)
        insert_notification(data)
        return {"status": "success"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/")
def read_root():
    return {"message": "Webhook, V1.1.0"}


if __name__ == "__main__":# or Run using: uvicorn cg-webhook:app --host 0.0.0.0 --port 8005 --reload
    import uvicorn
    uvicorn.run("cg-webhook:app", host="0.0.0.0", port=8005, reload=True)# dev
    #uvicorn.run(app, host="0.0.0.0", port=8005)# prod
