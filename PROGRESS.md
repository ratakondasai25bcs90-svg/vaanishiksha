kr# Progress Tracker

## Status: Module 1 - Project Scaffolding Complete

### Module 1: Recorded-lecture translation (IN PROGRESS)
- [x] Project scaffolding
  - [x] Backend structure (FastAPI)
  - [x] Frontend structure (React + TypeScript)
  - [x] Database models and migrations
  - [x] Redis/Celery setup for background jobs
  - [x] Dependency management (requirements.txt, package.json)
- [x] Authentication system (JWT-based, teacher/student roles)
- [x] Lecture upload API and storage handling
- [x] Background job infrastructure (Celery tasks)
- [x] ASR service (Whisper integration - ready to test)
- [x] Translation service (LLM-based with IndicTrans2 placeholder)
- [x] TTS service (gTTS for MVP)
- [x] Caching mechanism (check-cache-before-generate logic in API)
- [x] Student playback UI with language selector
- [x] Teacher dashboard (upload, view lectures)
- [x] Student dashboard (browse by grade, language indicators)
- [ ] **NEXT: End-to-end test (upload one lecture, dub to three languages)**
- [ ] Caption synchronization improvements
- [ ] Performance optimization

### Module 2: Auto worksheet generation (NOT STARTED)
- Waiting for Module 1 completion and verification

### Module 3: Live class real-time translation (NOT STARTED)
- Waiting for Module 2 completion

---

## Latest Changes (2026-09-25)
- Created complete backend API structure with FastAPI
- Implemented all database models (User, Lecture, DubbedLecture, Worksheet)
- Built authentication system with JWT and role-based access
- Created lecture upload endpoint with file handling
- Implemented Celery background job for dubbing pipeline (ASR → translate → TTS)
- Built React frontend with TypeScript, TailwindCSS, React Query
- Created three main views: Login/Register, Teacher Dashboard, Student Dashboard, Lecture Player
- Set up language selection and status polling for async dubbing jobs
- Added PWA support for offline capability
- Created setup script for Windows (setup.bat)

## Known Issues
1. **Database/Redis required** - PostgreSQL and Redis must be running before backend starts
2. **API keys needed** - GEMINI_API_KEY must be set in .env for translation to work
3. **IndicTrans2 not integrated** - Currently falls back to LLM translation (requires API key)
4. **Caption sync basic** - No word-level timestamp sync yet, just full transcript display
5. **No file validation** - Should add video/audio format validation and duration limits
6. **Storage local only** - Need to configure S3 for production

## Decisions Made
1. **TTS choice: gTTS for MVP** - Using Google TTS for initial version. Simple, supports all target languages, but quality could be better. Plan to integrate AI4Bharat IndicTTS later for better Indian language voices.
2. **Translation approach: LLM fallback** - IndicTrans2 integration deferred to focus on end-to-end flow first. Using Gemini API for now (requires API key). Will integrate IndicTrans2 once core pipeline is verified.
3. **Job queue: Celery with Redis** - Chose Celery for maturity and good Python integration. Using Redis as both broker and result backend.
4. **File storage: Local for dev** - Using filesystem storage for development. Configuration ready for S3 swap before production.
5. **ASR: faster-whisper** - Using faster-whisper instead of standard Whisper for better CPU performance.
6. **Frontend state: Zustand + React Query** - Zustand for auth state (persisted), React Query for server state and caching.
