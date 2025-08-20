from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import psycopg2
import os
from typing import Optional, Any, Dict

app = FastAPI()

DB_URL = os.getenv("DB_URL")


# Define the expected payload structure
class VisitorInfo(BaseModel):
    visitor_name: Optional[str]
    visitor_id: Optional[str]


class Notification(BaseModel):
    notification_time: str
    chat_id: str
    visitor_phone_number: Optional[str]
    messages: Any
    employee_full_name: Optional[str]
    visitor_info: Optional[VisitorInfo]
    status: Optional[str]


def insert_notification(data: Notification):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    query = """
    INSERT INTO whatsapp_notifications (
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
        data.notification_time,
        data.chat_id,
        data.visitor_phone_number,
        str(data.messages),  # stored as string (can be JSONB if needed)
        data.employee_full_name,
        data.visitor_info.visitor_name if data.visitor_info else None,
        data.visitor_info.visitor_id if data.visitor_info else None,
        data.status
    ))

    conn.commit()
    cur.close()
    conn.close()


@app.post("/webhook")
async def webhook(notification: Notification):
    try:
        insert_notification(notification)
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/")
def read_root():
    return {"message": "API, V1.1.0"}


if __name__ == "__main__":
    import uvicorn
    #uvicorn.run("cg-api:app", host="0.0.0.0", port=8005, reload=True)# dev
    uvicorn.run(app, host="0.0.0.0", port=8005)# prod
