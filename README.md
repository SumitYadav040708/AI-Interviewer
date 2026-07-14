
# 🧠 AI-Powered Technical Interview Prepper

A full-stack application designed to simulate real-world technical interviews. It allows users to practice answering conceptual and coding questions verbally and programmatically, receiving instant, AI-driven feedback on their performance.

## ✨ Key Features

- Customizable interviews for role, level, and question type
- Voice responses transcribed with OpenAI Whisper
- In-browser coding challenges with Monaco Editor
- AI-generated questions, follow-up prompts, scoring, and feedback
- Session history and analytics
- JWT-based authentication

## 🛠️ Tech Stack

### Frontend

- React (Vite)
- Redux Toolkit
- Tailwind CSS
- Monaco Editor
- Chart.js

### Backend

- Node.js and Express.js
- MongoDB with Mongoose
- JWT and bcryptjs

### AI Microservice

- Python 3.9+
- FastAPI
- Groq Cloud API via the official OpenAI-compatible SDK
- OpenAI Whisper
- PyDub / FFmpeg

## 🚀 Getting Started

### Prerequisites

1. Node.js (v16+) and npm
2. Python (v3.9+) and pip
3. MongoDB instance or Atlas URI
4. FFmpeg available on your system PATH
5. A Groq Cloud API key

### 1. Clone the Repository

```bash
git clone https://github.com/siddhantsaxenaofficial/ai-interviewer.git
cd ai-interviewer
```

### 2. Backend Setup

```bash
cd backend
npm install

# Create a .env file
echo "PORT=5000" > .env
echo "MONGO_URI=your_mongodb_connection_string" >> .env
echo "JWT_SECRET=your_jwt_secret" >> .env
echo "NODE_ENV=development" >> .env

npm run dev
```

### 3. AI Service Setup

```bash
cd ../ai-service

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

# Create a .env file
echo "AI_SERVICE_PORT=8000" > .env
echo "GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE" >> .env

python main.py
```

### 4. Frontend Setup

```bash
cd ../frontend
npm install

echo "VITE_API_URL=http://localhost:5000/api" > .env
npm run dev
```

### Or use the shortcut

```bat
for-first-time.bat
```

## 📐 Architecture Overview

1. Client (React) handles the interview UI, audio capture, and code editing.
2. The Node.js server manages authentication, database access, and session state.
3. The Python service receives AI tasks and calls the Groq Cloud API for question generation and answer evaluation.

## 🤝 Contributing

Contributions are welcome. Please fork the repository and submit a pull request.

## 📄 License

Distributed under the MIT License. See LICENSE for more information.