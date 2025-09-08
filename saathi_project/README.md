# Saathi - AI-First Mental Wellness Companion

Saathi is a comprehensive mental wellness platform designed specifically for college students, providing AI-powered conversations, mental health screening tools, and personalized support.

## 🌟 Features

- **AI Chat Interface**: ChatGPT-style conversation with crisis detection
- **Mental Health Screening**: PHQ-9, GAD-7, and GHQ assessments
- **Crisis Detection**: Real-time safety monitoring with escalation protocols
- **RAG-Powered Memory**: Persistent context using LlamaIndex and FAISS/Chroma
- **Firebase Integration**: Authentication, Firestore, and file storage
- **Privacy-First**: Explicit consent for data storage and PII protection
- **Voice Integration**: Speech-to-text and text-to-speech capabilities
- **Dark/Light Theme**: Persistent user preferences

## 🏗️ Architecture

### Frontend (React + Vite + Material UI)
- Modern React application with Material UI v5
- Firebase Authentication (Google + Email Magic Links)
- Real-time chat interface with typing indicators
- Responsive design with drawer navigation
- Theme persistence and accessibility features

### Backend (Django + DRF)
- Django REST Framework API
- LangGraph-style AI pipeline
- Llama-3.2-8B-Instruct integration via HuggingFace
- Crisis detection and safety protocols
- RAG document indexing and retrieval

### AI Pipeline Flow
```
User Message → Moderator → Crisis Detection → Memory/RAG → Therapist → Response
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.9+ and pip
- Firebase project (for authentication and storage)
- HuggingFace API key (optional, has fallbacks)

### 1. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your Firebase config
npm run dev
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python manage.py migrate
python manage.py runserver
```

### 3. Firebase Configuration
1. Create a Firebase project at https://console.firebase.google.com
2. Enable Authentication (Google + Email Link)
3. Enable Firestore Database
4. Enable Storage
5. Deploy security rules: `firebase deploy --only firestore:rules`

## 📝 Environment Variables

### Frontend (.env.local)
```
REACT_APP_API_BASE=http://localhost:8000
REACT_APP_FIREBASE_CONFIG={"apiKey":"...","authDomain":"..."}
REACT_APP_HUGGINGFACE_KEY=your_huggingface_key_optional
```

### Backend (.env)
```
SECRET_KEY=your_django_secret_key
DEBUG=True
HUGGINGFACE_API_KEY=your_huggingface_key_optional
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
FIREBASE_SERVICE_ACCOUNT=path/to/serviceAccountKey.json
```

## 🔗 API Endpoints

- `POST /api/chat/` - Main conversation endpoint
- `POST /api/transcribe/` - Speech-to-text transcription
- `POST /api/ingest-file/` - Document upload and indexing
- `POST /api/auth/send-otp/` - Email magic link (optional)
- `POST /api/auth/verify-otp/` - OTP verification (optional)

## 🧪 Testing

Run API tests:
```bash
cd backend/tests
python test_chat_api.py
python test_ingest_api.py
```

Run frontend tests:
```bash
cd frontend
npm test
```

## 📊 Mental Health Assessments

### PHQ-9 (Depression)
- 9 questions scoring 0-3 each
- Total score: 0-27
- Severity levels: Minimal (0-4), Mild (5-9), Moderate (10-14), Moderately Severe (15-19), Severe (20-27)

### GAD-7 (Anxiety)
- 7 questions scoring 0-3 each
- Total score: 0-21
- Severity levels: Minimal (0-4), Mild (5-9), Moderate (10-14), Severe (15-21)

### GHQ-12 (General Health)
- 12 questions with Likert scale
- Scoring method: 0-0-1-1 for each question
- Total score: 0-12

## 🔒 Privacy & Security

- All personal health information requires explicit consent
- Firestore security rules restrict access to user's own data
- Crisis detection includes immediate safety protocols
- PII logging is disabled by default
- Secure API key management with environment variables

## 🚨 Crisis Management

The system includes automated crisis detection for:
- Suicidal ideation
- Self-harm intentions
- Severe mental health episodes

When detected, the system:
1. Immediately provides crisis resources
2. Suggests emergency contacts
3. Logs incident for follow-up (with consent)
4. Does not continue regular therapy conversation

## 📱 Mobile Responsiveness

The application is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile devices
- PWA support (can be installed on mobile)

## 🔧 Development

### Code Structure
```
saathi_project/
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Route components
│   │   ├── services/      # API and Firebase services
│   │   └── utils/         # Helper functions
├── backend/               # Django backend
│   ├── api/               # Main API app
│   ├── saathi_backend/    # Django project settings
│   └── tests/             # API tests
└── infra/                 # Infrastructure configs
```

### Adding New Features
1. Frontend: Add components in `src/components/` or pages in `src/pages/`
2. Backend: Add views in `api/views.py` and URLs in `api/urls.py`
3. Update tests in respective test directories

## 🌐 Deployment

### Frontend (Vercel/Netlify)
```bash
npm run build
# Deploy dist/ folder to your hosting platform
```

### Backend (Railway/Heroku/DigitalOcean)
```bash
pip install gunicorn
gunicorn saathi_backend.wsgi:application
```

### Firebase
```bash
firebase init
firebase deploy
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📞 Support

For technical support or mental health resources:
- Crisis Text Line: Text HOME to 741741
- National Suicide Prevention Lifeline: 988
- Campus Counseling Services: Contact your university

## 🎯 Roadmap

- [ ] Group therapy sessions
- [ ] Peer support matching
- [ ] Wellness tracking and analytics
- [ ] Integration with campus health services
- [ ] Mobile app (React Native)
- [ ] Multi-language support

---

**Note**: This is a mental health support tool and should not replace professional therapy or emergency services. Always seek immediate help for crisis situations.