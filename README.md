# Aura Skincare Voice CX Agent — Aria

I built **Aria**, a browser-based voice customer-support agent for the DataStraw AI Voice Agent assessment. It helps Aura Skincare customers with order-related questions and company policies. It can talk in English and Hinglish, remember earlier messages during a call, and show the conversation transcript and a structured summary when the call ends.

## Features

- Customers can speak to Aria using their browser microphone.
- Aria replies using spoken audio.
- The interface shows when Aria is Listening, Thinking, or Speaking.
- Customers can choose English or Hinglish.
- Aria uses previous messages to answer follow-up questions.
- Order details are stored in a mock SQLite database.
- Backend tools handle order lookup, cancellation checks, shipping, returns, damaged products, and Cash on Delivery (COD) questions.
- The assistant follows the Aura Skincare policies and avoids guessing when order details are missing.
- Gemini is the main AI provider, and OpenRouter is used as a fallback.
- After a call, the app shows the transcript and a structured JSON summary.
- The app includes sample orders that can be used for testing.

## How It Works

```text
Customer
   |
   v
React + TypeScript + Vite frontend
   |-- Web Speech API converts speech to text
   |-- Shows the conversation and transcript
   |-- Reads Aria's replies aloud
   |
   | HTTP POST /chat
   v
FastAPI backend
   |-- Handles supported order and policy requests locally
   |-- Uses Gemini for AI responses
   |-- Uses OpenRouter if Gemini is unavailable
   |-- Runs approved backend tools
   |-- Reads mock order data from SQLite
   |
   v
Aria returns an answer based on the order or policy information
```

### Request flow

1. The customer speaks, and the browser converts the speech into text using the Web Speech API.
2. The frontend sends the message, selected language, and previous conversation messages to the backend's `/chat` endpoint.
3. If the message matches a supported order or policy workflow, the backend can handle it directly. Otherwise, Gemini can prepare a response or request an approved backend tool.
4. If Gemini fails, the backend tries OpenRouter. The fallback can use the same backend tools and conversation history.
5. The frontend displays Aria's response and reads it aloud. The message is also added to the transcript.
6. When the customer ends the call, the app shows the transcript and structured call summary.

Speech recognition and speech playback depend on browser support. For the demo, use a modern browser, allow microphone access, and test the deployed app over HTTPS.

## Technology Used

- **Frontend:** React, TypeScript, Vite
- **Voice:** Web Speech API for speech recognition and speech synthesis
- **Backend:** Python, FastAPI, Pydantic
- **Database:** SQLite and SQLAlchemy
- **AI:** Google Gemini with OpenRouter as a fallback
- **Testing:** pytest and the frontend production build

## Project Structure

```text
.
├── backend/
│   └── app/
│       ├── main.py
│       ├── schemas.py
│       ├── database.py
│       ├── models.py
│       ├── services/
│       │   ├── gemini_agent.py
│       │   ├── fallback_ai.py
│       │   ├── local_assistant.py
│       │   ├── policies.py
│       │   └── order_seed.py
│       └── tools/
│           └── orders.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── .env.example
├── .gitignore
└── README.md
```

This is the main structure. The project may also contain additional frontend components, hooks, utility files, and tests.

## Requirements

Before running the project, make sure you have:

- A Python version supported by the backend dependencies.
- Node.js and npm.
- A Gemini API key and an OpenRouter API key if you want to test both AI providers.
- A modern browser with microphone access.

## Environment Setup

Keep your API keys in a local `.env` file. **Do not commit real API keys to GitHub.**

Example project-root `.env` file:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional model overrides; use model names supported by your accounts
GEMINI_MODEL=your_supported_gemini_model
OPENROUTER_MODEL=your_supported_openrouter_model
```

For the frontend, create `frontend/.env.local` when needed:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

The `.env.example` file should contain placeholder values only. Never put Gemini or OpenRouter secret keys in a variable starting with `VITE_`, because frontend variables are visible in the browser.

For production, set `VITE_API_URL` to the public HTTPS URL of the deployed backend, without a trailing slash. This value is included when Vite builds the frontend, so the frontend needs to be redeployed after changing it.

## Run the Project Locally

### 1. Set up the backend

Run these commands from the project root.

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, use:

```bash
source .venv/bin/activate
```

Install the dependencies using the dependency file included in the repository. If `requirements.txt` is in the project root, run:

```bash
pip install -r requirements.txt
```

Create your `.env` file and add the required API keys. Then start the backend from the project root:

```bash
python -m uvicorn backend.app.main:app --reload
```

Useful backend endpoints:

- `GET /` — basic service status
- `GET /health` — health check
- `GET /docs` — interactive API documentation
- `GET /orders/{order_id}` — look up an order
- `POST /chat` — send a message to Aria

### 2. Set up the frontend

Open a second terminal and run:

```bash
cd frontend
npm install
```

If you need to set the backend URL locally, create `frontend/.env.local`:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the local URL shown in the terminal and allow microphone access when the browser asks for permission.

### 3. Run the tests and build

From the project root, activate the Python virtual environment and run:

```bash
python -m pytest backend/tests -v
```

To build the frontend, run:

```bash
cd frontend
npm run build
```

## Sample Orders and Policies

The app includes these sample orders for testing:

| Order ID  | Customer     | Product                     | Order value | Status           |
| --------- | ------------ | --------------------------- | ----------: | ---------------- |
| `ORD-101` | Priya Sharma | Vitamin C Serum (30ml)      |        ₹699 | Out for Delivery |
| `ORD-102` | Rahul Verma  | Hydrating Sunscreen SPF 50  |        ₹499 | Delivered        |
| `ORD-103` | Ananya Patel | Green Tea Face Wash + Toner |        ₹850 | Processing       |

The policies used by Aria are:

- **Shipping:** Orders above ₹499 qualify for free shipping. Orders below ₹499 have a ₹50 shipping fee. The policy does not say what happens for an order worth exactly ₹499, so Aria should not guess.
- **Delivery time:** Standard delivery takes 3–5 business days.
- **Returns:** Customers can request a return within 7 days of delivery if the product is unopened, unused, and in its original packaging.
- **Damaged or defective products:** Customers should report the issue within 48 hours and provide photos to request a replacement.
- **Cancellation:** An order can be cancelled only while its status is Processing. Shipped and Out for Delivery orders cannot be cancelled. Customers may refuse the delivery at the doorstep.
- **Cash on Delivery:** COD is available for orders up to ₹2,500. Customers can pay by cash or UPI.

These are mock orders for the assessment and demo, not real customer data. The app seeds the sample orders when it starts. On some hosting services, SQLite data may not remain saved after a restart or redeployment, so check that the sample orders are available after deployment.

## API Examples

Check whether the backend is running:

```bash
curl http://127.0.0.1:8000/health
```

Send a chat request:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you check order ORD-103?",
    "language": "english",
    "history": []
  }'
```

You can also try the endpoints using the interactive `/docs` page. In Windows PowerShell, `Invoke-RestMethod` can be used to send requests as well.

## Deployment

### Backend on Render

1. Push the project to GitHub.
2. Create a **Web Service** on Render and connect your repository.
3. Use the repository root as the Root Directory if `requirements.txt` and the `backend/` folder are both in the root.
4. If `requirements.txt` is in the repository root, use this build command:

   ```bash
   pip install -r requirements.txt
   ```

5. Use this start command:

   ```bash
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```

6. Add `GEMINI_API_KEY` and `OPENROUTER_API_KEY` in Render's environment settings. Add model override variables only if your code needs them.
7. After deployment, open the public `/health` and `/docs` URLs to check the backend.

Render's default filesystem is temporary. Since this project uses SQLite for sample orders, check that the orders are available after deployment and after a restart. A persistent or managed database would be a better choice if the app needed to keep real data.

### Frontend on Vercel

1. Import the same GitHub repository into Vercel.
2. Set the Root Directory to `frontend`.
3. Use `npm run build` as the build command and `dist` as the output directory, if Vercel does not detect them automatically.
4. Add `VITE_API_URL` and set it to the public Render backend URL, without a trailing slash.
5. Deploy the frontend and open the public URL.
6. In the backend CORS settings, add the exact Vercel website origin, for example `https://your-project.vercel.app`. Replace this example with the actual deployed URL.
7. Redeploy the backend after changing CORS. Redeploy the frontend after changing `VITE_API_URL`.

### Test the deployed app

Before sharing the links, check the following:

- Open the public website over HTTPS and allow microphone access.
- Test speech input and spoken responses.
- Try the sample orders `ORD-101`, `ORD-102`, and `ORD-103`.
- Ask at least one policy question.
- Try an invalid order ID to check that Aria does not invent order details.
- Ask a follow-up question to check whether the conversation history is used.
- Test both English and Hinglish.
- End the call and check the transcript and structured summary.
- Test the OpenRouter fallback.
- If something fails, check the browser's Console and Network tabs and the backend deployment logs.

## Troubleshooting

- **The frontend cannot connect to the backend:** Check `VITE_API_URL`, make sure the backend `/health` endpoint works, and confirm that the frontend's exact URL is allowed in the backend CORS settings. Redeploy the frontend after changing `VITE_API_URL`.
- **The microphone does not work:** Allow microphone access, use HTTPS for the deployed app, and try a browser that supports the Web Speech API.
- **AI responses fail:** Check the API keys and backend logs. Also check that the configured OpenRouter model supports the tool-calling features used by the app.
- **A sample order is missing:** Check the backend logs and confirm that the sample-order seeding code ran.
- **I need to fix something after deployment:** I can make the change locally, run the tests and build, push the update to GitHub, and then test the redeployed app again.

## Testing Checklist

Before submission, I check that:

- [ ] `python -m pytest backend/tests -v` passes.
- [ ] `npm run build` passes from the `frontend/` directory.
- [ ] The backend `/health` endpoint works.
- [ ] Valid and invalid order IDs are handled correctly.
- [ ] Policy answers follow the rules listed above.
- [ ] Follow-up messages can use the conversation history.
- [ ] English and Hinglish modes work.
- [ ] Gemini and the OpenRouter fallback have been tested.
- [ ] The transcript and structured summary appear after a call.
- [ ] The public website works over HTTPS.
- [ ] No real API keys or other secrets are committed to GitHub.

## Section 9 — My Answers

### 1. Why did you choose this architecture and technology stack?

I wanted to build a voice support agent that customers could use directly in their browser. So, I used React, TypeScript, and Vite for the frontend and FastAPI for the backend. The Web Speech API helped me add voice input and spoken replies without needing a separate telephony system. I kept order details and policy checks on the backend so that Aria could give answers based on actual data instead of depending only on the AI model. I also added OpenRouter as a fallback so the application could try another AI provider if Gemini failed.

### 2. What was the most difficult part, and how did you solve it?

The main challenge was making sure Aria could handle a conversation naturally while giving correct answers about orders and company policies.Another challange was to make sure it understand what customer is trying to aksand reply accordingly. An AI model can sometimes give incorrect information, so I kept the important order and policy checks in the backend. When more information was needed, the AI could request the available backend tools. And also passed previous messages to the backend so Aria could understand follow-up questions. Then tested these features to check that the conversation and order-related responses worked as expected.

### 3. If you had one more week, what would you improve first and why?

I would first improve the voice experience because it is the main part of this application. Then I would work on context understand understanding and how to handle customers input.Currently i used gemini api and OpenRouter api but both has rate limit . Once exceded that might stop giving answers. So I would have worked on that to find the solution . And if possible tried to use RAG to read the policies documents of company and used LLM for replying customers. I would work on handling interruptions, reducing response delays, and improving what happens when the browser cannot recognise speech properly. I would also test the application on more browsers. These improvements would make conversations smoother and help customers use Aria more easily.

### 4. What would need to change for 1,000 customer conversations a day?

### 4. What would need to change for 1,000 customer conversations a day?

For 1,000 conversations a day, I would first make sure the backend can handle multiple customers at the same time without slowing down or failing. Then I would move the order data from SQLite to a managed database that can handle more requests reliably. And also improve the AI request handling by adding timeouts, retries, and proper fallback handling if a provider fails. To avoid overloading the application, I would add rate limits and monitor response times, errors, and database performance. Finally, I would test the application with many requests at once to find and fix performance issues before handling real customer traffic.

## Demo Video and Submission

The assessment asks for a 3–5 minute demo video. My demo should show:

1. Aria having a voice conversation.
2. At least one order lookup.
3. One question about an Aura Skincare policy.
4. The transcript and structured summary after the call.
5. A short explanation of how the frontend, backend, AI providers, and order database work together.

### Submission email

- **To:** `ozair.shaikh@datastraw.in`, `aryan.jaiswal@datastraw.in`
- **CC:** `talent@datastraw.in`
- **Subject:** `AI Voice Agent Assignment - [Your Full Name]`

The email should include:

- Public application URL
- Public GitHub repository URL
- Demo video link
- LinkedIn profile URL
- A short approach note

### Approach Note

I built Aria as a browser-based voice support agent using React, TypeScript, FastAPI, and the Web Speech API. It uses Gemini for AI responses and OpenRouter as a fallback, while the backend checks order details and Aura Skincare policies using mock SQLite data. The app also keeps conversation history and shows a transcript and structured summary after each call.
