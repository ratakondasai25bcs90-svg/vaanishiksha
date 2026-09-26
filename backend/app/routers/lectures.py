from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel
import os
import shutil
from app.database import get_db
from app.models import User, Lecture, DubbedLecture, UserRole
from app.routers.auth import get_current_user
from app.config import settings
from app.tasks import process_lecture_dubbing

router = APIRouter()


class LectureCreate(BaseModel):
    title: str
    description: str | None = None
    subject: str | None = None
    grade_level: int | None = None
    original_language: str


class LectureResponse(BaseModel):
    id: int
    title: str
    description: str | None
    subject: str | None
    grade_level: int | None
    original_language: str
    duration_seconds: int | None
    created_at: datetime
    has_transcript: bool
    available_languages: List[str]


class DubbedLectureResponse(BaseModel):
    id: int
    lecture_id: int
    target_language: str
    status: str
    dubbed_audio_url: str | None
    transcript_url: str | None
    created_at: datetime
    completed_at: datetime | None


@router.post("/upload", response_model=LectureResponse)
async def upload_lecture(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    subject: str = Form(None),
    grade_level: int = Form(None),
    original_language: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can upload lectures")
    
    # Validate file type
    allowed_extensions = ['.mp4', '.mp3', '.wav', '.m4a', '.webm']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not supported. Allowed: {allowed_extensions}")
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = f"{settings.storage_path}/lectures/{safe_filename}"
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create lecture record
    lecture = Lecture(
        teacher_id=current_user.id,
        title=title,
        description=description,
        subject=subject,
        grade_level=grade_level,
        original_language=original_language,
        original_file_path=file_path
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    
    return {
        "id": lecture.id,
        "title": lecture.title,
        "description": lecture.description,
        "subject": lecture.subject,
        "grade_level": lecture.grade_level,
        "original_language": lecture.original_language,
        "duration_seconds": lecture.duration_seconds,
        "created_at": lecture.created_at,
        "has_transcript": lecture.transcript_text is not None,
        "available_languages": []
    }


@router.get("/", response_model=List[LectureResponse])
async def list_lectures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.TEACHER:
        lectures = db.query(Lecture).filter(Lecture.teacher_id == current_user.id).all()
    else:
        lectures = db.query(Lecture).all()
    
    result = []
    for lecture in lectures:
        available_languages = [dub.target_language for dub in lecture.dubbed_versions if dub.status == "completed"]
        result.append({
            "id": lecture.id,
            "title": lecture.title,
            "description": lecture.description,
            "subject": lecture.subject,
            "grade_level": lecture.grade_level,
            "original_language": lecture.original_language,
            "duration_seconds": lecture.duration_seconds,
            "created_at": lecture.created_at,
            "has_transcript": lecture.transcript_text is not None,
            "available_languages": available_languages
        })
    
    return result


@router.get("/{lecture_id}", response_model=LectureResponse)
async def get_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    available_languages = [dub.target_language for dub in lecture.dubbed_versions if dub.status == "completed"]
    
    return {
        "id": lecture.id,
        "title": lecture.title,
        "description": lecture.description,
        "subject": lecture.subject,
        "grade_level": lecture.grade_level,
        "original_language": lecture.original_language,
        "duration_seconds": lecture.duration_seconds,
        "created_at": lecture.created_at,
        "has_transcript": lecture.transcript_text is not None,
        "available_languages": available_languages
    }


@router.post("/{lecture_id}/dub/{target_language}", response_model=DubbedLectureResponse)
async def request_dubbed_lecture(
    lecture_id: int,
    target_language: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate language
    if target_language not in settings.supported_languages:
        raise HTTPException(status_code=400, detail=f"Language not supported. Supported: {settings.supported_languages}")
    
    # Get lecture
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    # Check if dubbed version already exists
    existing_dub = db.query(DubbedLecture).filter(
        DubbedLecture.lecture_id == lecture_id,
        DubbedLecture.target_language == target_language
    ).first()
    
    if existing_dub:
        dubbed_audio_url = f"/storage/dubbed/{os.path.basename(existing_dub.dubbed_audio_path)}" if existing_dub.status == "completed" else None
        transcript_url = f"/storage/transcripts/{os.path.basename(existing_dub.translated_transcript_path)}" if existing_dub.translated_transcript_path else None
        
        return {
            "id": existing_dub.id,
            "lecture_id": existing_dub.lecture_id,
            "target_language": existing_dub.target_language,
            "status": existing_dub.status,
            "dubbed_audio_url": dubbed_audio_url,
            "transcript_url": transcript_url,
            "created_at": existing_dub.created_at,
            "completed_at": existing_dub.completed_at
        }
    
    # Create new dubbing job
    dubbed_lecture = DubbedLecture(
        lecture_id=lecture_id,
        target_language=target_language,
        dubbed_audio_path="",  # Will be set by worker
        status="pending"
    )
    db.add(dubbed_lecture)
    db.commit()
    db.refresh(dubbed_lecture)
    
    # Queue background job
    process_lecture_dubbing.delay(dubbed_lecture.id)
    
    return {
        "id": dubbed_lecture.id,
        "lecture_id": dubbed_lecture.lecture_id,
        "target_language": dubbed_lecture.target_language,
        "status": dubbed_lecture.status,
        "dubbed_audio_url": None,
        "transcript_url": None,
        "created_at": dubbed_lecture.created_at,
        "completed_at": None
    }


@router.get("/{lecture_id}/dub/{target_language}/status", response_model=DubbedLectureResponse)
async def get_dubbing_status(
    lecture_id: int,
    target_language: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dubbed_lecture = db.query(DubbedLecture).filter(
        DubbedLecture.lecture_id == lecture_id,
        DubbedLecture.target_language == target_language
    ).first()
    
    if not dubbed_lecture:
        raise HTTPException(status_code=404, detail="Dubbed version not found")
    
    dubbed_audio_url = f"/storage/dubbed/{os.path.basename(dubbed_lecture.dubbed_audio_path)}" if dubbed_lecture.status == "completed" else None
    transcript_url = f"/storage/transcripts/{os.path.basename(dubbed_lecture.translated_transcript_path)}" if dubbed_lecture.translated_transcript_path else None
    
    return {
        "id": dubbed_lecture.id,
        "lecture_id": dubbed_lecture.lecture_id,
        "target_language": dubbed_lecture.target_language,
        "status": dubbed_lecture.status,
        "dubbed_audio_url": dubbed_audio_url,
        "transcript_url": transcript_url,
        "created_at": dubbed_lecture.created_at,
        "completed_at": dubbed_lecture.completed_at
    }
