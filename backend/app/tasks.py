from celery import Celery
from app.config import settings
from app.database import SessionLocal
from app.models import Lecture, DubbedLecture
from datetime import datetime
import os

celery_app = Celery(
    "tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)


@celery_app.task
def process_lecture_dubbing(dubbed_lecture_id: int):
    """
    Background task to process lecture dubbing:
    1. Generate transcript if not exists (ASR)
    2. Translate transcript
    3. Generate dubbed audio (TTS)
    4. Save and update database
    """
    db = SessionLocal()
    try:
        dubbed_lecture = db.query(DubbedLecture).filter(DubbedLecture.id == dubbed_lecture_id).first()
        if not dubbed_lecture:
            return {"error": "Dubbed lecture not found"}
        
        dubbed_lecture.status = "processing"
        db.commit()
        
        lecture = dubbed_lecture.lecture
        target_language = dubbed_lecture.target_language
        
        # Step 1: Generate transcript if needed
        if not lecture.transcript_text:
            from app.services.asr_service import transcribe_audio
            transcript_text = transcribe_audio(lecture.original_file_path, lecture.original_language)
            
            # Save transcript
            transcript_filename = f"transcript_{lecture.id}_{lecture.original_language}.txt"
            transcript_path = f"{settings.storage_path}/transcripts/{transcript_filename}"
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            
            lecture.transcript_text = transcript_text
            lecture.transcript_path = transcript_path
            db.commit()
        
        # Step 2: Translate transcript
        from app.services.translation_service import translate_text
        translated_text = translate_text(
            lecture.transcript_text,
            source_lang=lecture.original_language,
            target_lang=target_language
        )
        
        # Save translated transcript
        translated_transcript_filename = f"transcript_{lecture.id}_{target_language}.txt"
        translated_transcript_path = f"{settings.storage_path}/transcripts/{translated_transcript_filename}"
        with open(translated_transcript_path, "w", encoding="utf-8") as f:
            f.write(translated_text)
        
        dubbed_lecture.translated_transcript_text = translated_text
        dubbed_lecture.translated_transcript_path = translated_transcript_path
        
        # Step 3: Generate dubbed audio
        from app.services.tts_service import text_to_speech
        dubbed_audio_filename = f"dubbed_{lecture.id}_{target_language}.wav"
        dubbed_audio_path = f"{settings.storage_path}/dubbed/{dubbed_audio_filename}"
        
        text_to_speech(translated_text, target_language, dubbed_audio_path)
        
        dubbed_lecture.dubbed_audio_path = dubbed_audio_path
        dubbed_lecture.status = "completed"
        dubbed_lecture.completed_at = datetime.utcnow()
        db.commit()
        
        return {"status": "completed", "dubbed_lecture_id": dubbed_lecture_id}
    
    except Exception as e:
        dubbed_lecture.status = "failed"
        db.commit()
        return {"error": str(e)}
    
    finally:
        db.close()
