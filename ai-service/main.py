import uvicorn
import os
import io
import json
import re
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
from openai import OpenAI
import whisper

load_dotenv()

AI_SERVICE_PORT = int(os.getenv("AI_SERVICE_PORT", 8000))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

app = FastAPI(title="AI Interviewer Microservice", version="1.0")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WHISPER_MODEL = None

try:
    print("Loading Whisper Model ...")
    WHISPER_MODEL = whisper.load_model("base.en")
    print("Whisper Model Loaded Successfully")
except Exception as e:
    print("Error while loading Whisper Model")
    print(e)


class QuestionResquest(BaseModel):
    role: str = "MERN Stack Developer"
    level: str = "Junior"
    count: int = 5
    interview_type: str = "coding-mix"


class QuestionResponse(BaseModel):
    questions: list[str]
    model_used: str


class EvaluationRequest(BaseModel):
    question: str
    question_type: str
    role: str
    level: str
    user_answer: Optional[str] = None
    user_code: Optional[str] = None


class EvaluationResponse(BaseModel):
    technicalScore: int
    confidenceScore: int
    aiFeedback: str
    idealAnswer: str


def create_groq_client() -> OpenAI:
    if not GROQ_API_KEY or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        raise RuntimeError("GROQ_API_KEY is not configured. Set it in the environment or ai-service/.env.")
    return OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")


def call_groq(messages, temperature: float = 0.7) -> str:
    groq_client = create_groq_client()
    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )
    return completion.choices[0].message.content or ""


@app.get("/")
async def root():
    return {
        "message": "Hello from AI Interviewer Microservice !",
        "provider": "groq",
        "model": GROQ_MODEL_NAME,
    }


@app.post("/generate-questions", response_model=QuestionResponse)
async def generate_questions(request: QuestionResquest):
    try:
        if request.interview_type == "coding-mix":
            coding_count = int(request.count * 0.2)
            oral_oral = int(request.count) - int(coding_count)

            instruction = (
                f"The first {coding_count} questions MUST be coding challenge requiring function implementation."
                f"The remaining {oral_oral} questions MUST be conceptual oral questions."
            )
        else:
            instruction = "All questions MUST be conceptual oral questions. Do Not generate any coding or implementation challenges."

        system_prompt = (
            "You are a professional technical interviewer. "
            "Task: Generate interview questions. No conversational text or numbering. "
            f"Crucial: {instruction}"
            "Output exactly one question per line. "
        )

        user_prompt = (
            f"Generate exactly {request.count} unique interview questions for a {request.level} level {request.role} "
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response_text = call_groq(messages, temperature=0.6).strip()
        questions = [q.strip() for q in response_text.split("\n") if q.strip()]
        return QuestionResponse(questions=questions[:request.count], model_used=GROQ_MODEL_NAME)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_audio_path = None
    try:
        audio_bytes = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            temp_audio_path = tmp.name
            tmp.write(audio_bytes)

        if not WHISPER_MODEL:
            raise HTTPException(status_code=503, detail="Whisper Model is not loaded")

        result = WHISPER_MODEL.transcribe(temp_audio_path)
        transcription = ""
        if isinstance(result, dict):
            transcription = str(result.get("text", ""))
        elif isinstance(result, list) and result:
            first_item = result[0]
            if isinstance(first_item, dict):
                transcription = str(first_item.get("text", ""))
            else:
                transcription = str(first_item)
        else:
            transcription = str(result)

        return {"transcription": transcription.strip()}

    except Exception as e:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    try:
        if request.question_type == "oral":
            assessment_instruction = (
                "This is a conceptual oral question. Focus purely on candidate's verbal explanation. "
                "Ignore any code blocks. "
                "CRITICAL: If the transcript is empty, nonsense (e.g. 'blah blah','testing') or irrelevant to the question, SCORE 0."
            )
        else:
            assessment_instruction = (
                "This is a coding challenge question. Evaluate the code logic and efficiency. "
                "Use the transcription only for insight into their thought process. "
                "CRITICAL: If the code is 'undefined', empty, just random comments, or random characters, SCORE 0."
            )

        system_prompt = (
            "You are a strict technical interviewer. "
            "Do NOT hallucinate positive reviews for bad input. "
            "RULE 1: If the answer is gibberish, irrelevant, or missing, return technicalScore:0 and confidenceScore:0. "
            "RULE 2: For idealAnswer, provide a clean Markdown string. Do NOT return a nested JSON object. "
            f"Context: {assessment_instruction}"
            "Return ONLY valid JSON. "
            "Do not use markdown, do not wrap the response in ```json, do not add explanations, and do not add any additional text. "
            "Required keys: technicalScore (0-100), confidenceScore (0-100), aiFeedback, idealAnswer. "
        )
        user_prompt = (
            f"Role: {request.role}\n"
            f"Question: {request.question}\n"
            f"Level: {request.level}\n"
            f"Verbal Answer: {request.user_answer or 'No verbal answer provided'}\n"
            f"Code Answer: {request.user_code or 'No code provided'}\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response_text = call_groq(messages, temperature=0.1).strip()
        print("Raw evaluation response:", response_text)

        def extract_json(text: str) -> str:
            # Remove code fences and leading/trailing noise around JSON
            text = re.sub(r'```(?:json)?', '', text, flags=re.IGNORECASE)
            # Find the first and last JSON object delimiters
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                return text[start:end+1]
            return text

        cleaned_response = extract_json(response_text)

        try:
            evaluation_data = json.loads(cleaned_response)
            if 'idealAnswer' in evaluation_data and not isinstance(evaluation_data['idealAnswer'], str):
                evaluation_data['idealAnswer'] = json.dumps(evaluation_data['idealAnswer'])
            return EvaluationResponse(**evaluation_data)
        except json.JSONDecodeError as first_error:
            cleaned_response = re.sub(r'[\r\n\t]+', ' ', cleaned_response).strip()
            try:
                evaluation_data = json.loads(cleaned_response)
                if 'idealAnswer' in evaluation_data and not isinstance(evaluation_data['idealAnswer'], str):
                    evaluation_data['idealAnswer'] = json.dumps(evaluation_data['idealAnswer'])
                return EvaluationResponse(**evaluation_data)
            except Exception as second_error:
                print("Failed to parse response:", response_text)
                print("Cleaned response:", cleaned_response)
                print("First JSON error:", first_error)
                print("Second JSON error:", second_error)
                return EvaluationResponse(technicalScore=0, confidenceScore=0, aiFeedback="Failed to parse response", idealAnswer="Failed to parse response")

    except Exception as e:
        print(f"Failed to generate response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=AI_SERVICE_PORT)