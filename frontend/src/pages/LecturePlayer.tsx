import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useAuthStore } from '../stores/authStore'
import api from '../lib/api'

interface Lecture {
  id: number
  title: string
  description: string
  subject: string
  grade_level: number
  original_language: string
  available_languages: string[]
}

interface DubbedLecture {
  id: number
  lecture_id: number
  target_language: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  dubbed_audio_url: string | null
  transcript_url: string | null
}

const LANGUAGES: Record<string, string> = {
  en: 'English',
  hi: 'हिन्दी',
  ta: 'தமிழ்',
  te: 'తెలుగు',
  kn: 'ಕನ್ನಡ',
  bn: 'বাংলা',
}

export default function LecturePlayer() {
  const { lectureId } = useParams<{ lectureId: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [selectedLanguage, setSelectedLanguage] = useState(user?.preferred_language || 'en')
  const [transcript, setTranscript] = useState('')
  const audioRef = useRef<HTMLAudioElement>(null)

  const { data: lecture, isLoading: lectureLoading } = useQuery({
    queryKey: ['lecture', lectureId],
    queryFn: async () => {
      const response = await api.get<Lecture>(`/lectures/${lectureId}`)
      return response.data
    },
  })

  const requestDubMutation = useMutation({
    mutationFn: async (language: string) => {
      const response = await api.post<DubbedLecture>(
        `/lectures/${lectureId}/dub/${language}`
      )
      return response.data
    },
  })

  const { data: dubbedLecture, refetch: refetchDubStatus } = useQuery({
    queryKey: ['dubbed-lecture', lectureId, selectedLanguage],
    queryFn: async () => {
      const response = await api.get<DubbedLecture>(
        `/lectures/${lectureId}/dub/${selectedLanguage}/status`
      )
      return response.data
    },
    enabled: false,
  })

  // Poll for status if processing
  useEffect(() => {
    if (dubbedLecture?.status === 'processing' || dubbedLecture?.status === 'pending') {
      const interval = setInterval(() => {
        refetchDubStatus()
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [dubbedLecture?.status, refetchDubStatus])

  // Fetch dubbed version when language changes
  useEffect(() => {
    if (selectedLanguage && lecture) {
      if (lecture.available_languages.includes(selectedLanguage)) {
        refetchDubStatus()
      } else {
        // Request new dubbing
        requestDubMutation.mutate(selectedLanguage, {
          onSuccess: (data) => {
            // Start polling
            refetchDubStatus()
          },
        })
      }
    }
  }, [selectedLanguage, lecture])

  // Load transcript
  useEffect(() => {
    if (dubbedLecture?.transcript_url) {
      fetch(dubbedLecture.transcript_url)
        .then((res) => res.text())
        .then((text) => setTranscript(text))
        .catch(console.error)
    }
  }, [dubbedLecture?.transcript_url])

  if (lectureLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Loading lesson...</p>
        </div>
      </div>
    )
  }

  if (!lecture) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl text-gray-600">Lesson not found</p>
          <button onClick={() => navigate(-1)} className="btn btn-primary mt-4">
            Go Back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <button onClick={() => navigate(-1)} className="text-primary-600 hover:text-primary-700">
            ← Back to lessons
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="card mb-6">
          <div className="mb-4">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-bold mb-2">{lecture.title}</h1>
                <p className="text-gray-600">{lecture.description}</p>
              </div>
              <div className="bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-sm font-medium">
                Class {lecture.grade_level}
              </div>
            </div>
          </div>

          {/* Language selector */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Listen in:</label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="w-full md:w-64 px-4 py-3 border-2 border-gray-300 rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {Object.entries(LANGUAGES).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          {/* Audio player and status */}
          <div className="bg-gray-50 rounded-lg p-6">
            {dubbedLecture?.status === 'completed' && dubbedLecture.dubbed_audio_url ? (
              <div>
                <audio
                  ref={audioRef}
                  controls
                  className="w-full"
                  src={dubbedLecture.dubbed_audio_url}
                >
                  Your browser does not support the audio element.
                </audio>
              </div>
            ) : dubbedLecture?.status === 'processing' || dubbedLecture?.status === 'pending' ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mb-4"></div>
                <p className="text-lg font-medium text-gray-700">
                  Preparing your lesson in {LANGUAGES[selectedLanguage]}...
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  This usually takes 1-2 minutes. Please wait.
                </p>
              </div>
            ) : dubbedLecture?.status === 'failed' ? (
              <div className="text-center py-8">
                <p className="text-lg font-medium text-red-600">
                  Sorry, something went wrong. Please try again.
                </p>
                <button
                  onClick={() => requestDubMutation.mutate(selectedLanguage)}
                  className="btn btn-primary mt-4"
                >
                  Retry
                </button>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-lg font-medium text-gray-700">
                  Preparing your lesson...
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Transcript/captions */}
        {transcript && dubbedLecture?.status === 'completed' && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Transcript</h2>
            <div className="prose max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{transcript}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
