from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from fastapi.staticfiles import StaticFiles
from app.extentions import db  
from app.models import VideoReview, Video
from fastapi.middleware.cors import CORSMiddleware  
import logging
import asyncio
import openai
import json
import requests
from app import create_app  

openai.api_key = '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'
IP_PORT = 8445
IP = "54.226.79.143"

# Create Flask app instance
flask_app = create_app()

# Create FastAPI app
app = FastAPI()

# Add CORS middleware with wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Static Files Mount
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Navigate to /static/index.html to access the chat interface"}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

def generate_chat_history(candidates):

    # Formatting candidate data
    candidate_data = "\n".join(
        f"**Candidate {i+1}**\n"
        f"- Name: {candidate['candidate_name']}\n"
        f"- Body Language_score: {candidate['body_language']}\n"
        f"- Confidence_score: {candidate['confidence']}\n"
        f"- Engagement with Interviewers score: {candidate['engagement_with_interviewers']}\n"
        f"- Leadership Traits score: {candidate['leadership_traits']}\n"
        f"- Key Attributes: {candidate['five_key_attributes']}\n"
        f"- Interview Summary: {candidate['interview_summary']}\n"
        for i, candidate in enumerate(candidates)
    )

    # Constructing the user message
    user_message = f"""
    You are an AI assistant analyzing and comparing candidates for a project role based on the following data. Answer HR’s questions in a brief, clear, and human-like manner. Focus on the most relevant attributes and provide concise reasoning. When comparing candidates, justify the recommendation with key points but keep it short and direct.

    Candidate Data:
    {candidate_data}

    Sample Question:
"Which candidate would be more reliable in dealing with a project?"

Sample Answer:
Candidate 1 is more reliable due to stronger leadership and confidence. They also engaged better during the interview, showing solid interpersonal skills. Candidate 2 performed well but fell slightly short on leadership."""

    chat_history = {
        "role": "user",
        "content": user_message
    }

    return chat_history


# GPT Streaming Response generator
async def get_gpt_response(data, previous_conversation: List[dict], websocket: WebSocket, model: str = "gpt-4o-mini"):
    previous_conversation.append({"role": "user", "content": data})
    logging.info(previous_conversation)
    delay_per_token = 0.15  # Delay between each token (in seconds)
    # OpenAI stream response with stream=True
    response = openai.chat.completions.create(
        model=model,
        messages=previous_conversation,
        temperature=0.7,
        max_tokens=4096,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    collected_message = ""  # To collect full message for history
    logging.info(response.choices[0].message.content)
    await websocket.send_text(response.choices[0].message.content)
    # try:
    #     # Iterate over the streamed chunks
    #     for chunk in response:

    #         # Extract the `delta` object (containing the message)
            
    #         token = chunk.choices[0].delta.content
            
    #         if token:
    #             logging.info(f"Token received: {token}")
    #             collected_message +=  token # Append the token to the full message
    #             # await websocket.send_text(token)  # Stream the token to the WebSocket
    #             # await asyncio.sleep(delay_per_token)
    #         else:
    #             logging.info("No content in this chunk.")

    # await websocket.send_text("<EOM>")

    # except Exception as e:
    #     logging.error(f"Error while streaming response: {e}")

    # Append the full message from GPT to the conversation history
    previous_conversation.append({"role": "assistant", "content": collected_message})

    return collected_message, previous_conversation


# Connection Manager instance
manager = ConnectionManager()

@app.websocket("/api/v1/chat")
async def websocket_endpoint(websocket: WebSocket, payload):
    
    await manager.connect(websocket)
    logging.info(payload)
    try:
        payload = json.loads(payload)
        # Extract video IDs from the payload
        video_ids = payload.get("video_ids", [])
        if not video_ids:
            logging.info("No video IDs provided in the payload.")
            await manager.send_personal_message("No video IDs provided.", websocket)
            await manager.disconnect(websocket)
            return

        # Flask context must be pushed to access the database
        with flask_app.app_context():
            candidate_data = db.session.query(VideoReview, Video
            ).join(
                Video, VideoReview.video_id == Video.id
            ).filter(
                Video.id.in_(video_ids)
            ).all()

            if not candidate_data:
                logging.info(f"No matching candidates for video IDs: {video_ids}")
                await manager.send_personal_message("No matching candidates found.", websocket)
                await manager.disconnect(websocket)
                return

            candidates_info = []
            for review, video in candidate_data:
                candidate_info = {
                    "candidate_name": review.candidate_name,
                    "body_language": review.body_language,
                    "eye_contact_with_interviewers": review.eye_contact_with_interviewers,
                    "confidence": review.confidence,
                    "vocabulary_and_grammar": review.vocabulary_and_grammar,
                    "engagement_with_interviewers": review.engagement_with_interviewers,
                    "leadership_traits": review.leadership_traits,
                    "candidate_gender": review.candidate_gender,
                    "candidate_attire": review.candidate_attire,
                    "native_english_speaker": review.native_english_speaker,
                    "interview_summary": review.interview_summary,
                    "overall_score": review.overall_score,
                    "five_key_attributes": review.five_key_attributes,
                    "video_url": video.video_url
                }
                candidates_info.append(candidate_info)

        # Initialize conversation history with the prompt
        conversation_history = []
        prompt = generate_chat_history(candidates_info)
        conversation_history.append(prompt)

        await manager.send_personal_message("Welcome to the interview analysis! Please ask your questions.", websocket)
        chat_history = {"interview_transcript": []}

        while True:
            data = await websocket.receive_text()
            chat_history["interview_transcript"].append({"hr": data})

            gpt_response, conversation_history = await get_gpt_response(data, conversation_history, websocket)

            chat_history["interview_transcript"].append({"gpt": gpt_response})
            await manager.send_personal_message(f"GPT: {gpt_response}", websocket)
            
            await manager.send_personal_message("<EOM>", websocket)
        # upload_transcript(chat_history, video_ids)

    except Exception as e:
        logging.error(f"Error in WebSocket endpoint: {e}")
        await manager.disconnect(websocket)
        await manager.broadcast("A user has disconnected.")

    

# Running the FastAPI application with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=IP_PORT)
