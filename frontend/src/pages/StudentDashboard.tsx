import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../stores/authStore'
import api from '../lib/api'

interface Lecture {
  id: number
  title: string
  description: string
  subject: string
  grade_level: number
  original_language: string
  created_at: string
  has_transcript: boolean
  available_languages: string[]
}

const LANGUAGE_ICONS: Record<string, string> = {
  en: '🇬🇧',
  hi: '🇮🇳',
  ta: '🇮🇳',
  te: '🇮🇳',
  kn: '🇮🇳',
  bn: '🇮🇳',
}

export default function StudentDashboard() {
  const { user, logout } = useAuthStore()
  const [selectedGrade, setSelectedGrade] = useState<number | 'all'>(user?.grade_level || 'all')

  const { data: lectures, isLoading } = useQuery({
    queryKey: ['lectures'],
    queryFn: async () => {
      const response = await api.get<Lecture[]>('/lectures/')
      return response.data
    },
  })

  const filteredLectures = lectures?.filter((lecture) => {
    if (selectedGrade === 'all') return true
    return lecture.grade_level === selectedGrade
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-primary-700">My Learning</h1>
            <p className="text-sm text-gray-600">Welcome, {user?.full_name}!</p>
          </div>
          <button onClick={logout} className="btn btn-secondary">
            Logout
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Grade filter */}
        <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedGrade('all')}
            className={`px-4 py-2 rounded-full font-medium whitespace-nowrap ${
              selectedGrade === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            All Classes
          </button>
          {[1, 2, 3, 4, 5, 6, 7, 8].map((grade) => (
            <button
              key={grade}
              onClick={() => setSelectedGrade(grade)}
              className={`px-4 py-2 rounded-full font-medium whitespace-nowrap ${
                selectedGrade === grade
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Class {grade}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600">Loading lessons...</p>
          </div>
        ) : filteredLectures && filteredLectures.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredLectures.map((lecture) => (
              <Link
                key={lecture.id}
                to={`/lecture/${lecture.id}`}
                className="card hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-sm font-medium">
                    Class {lecture.grade_level}
                  </div>
                  {lecture.available_languages.includes(user?.preferred_language || 'en') && (
                    <div className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
                      ✓ Your language
                    </div>
                  )}
                </div>

                <h3 className="font-bold text-lg mb-2 line-clamp-2">{lecture.title}</h3>
                
                {lecture.description && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">{lecture.description}</p>
                )}

                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <span className="text-sm font-medium text-gray-700">{lecture.subject || 'General'}</span>
                  
                  <div className="flex gap-1">
                    {lecture.available_languages.length > 0 ? (
                      lecture.available_languages.slice(0, 3).map((lang) => (
                        <span key={lang} className="text-lg" title={lang}>
                          {LANGUAGE_ICONS[lang] || '🌐'}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-500">Original only</span>
                    )}
                  </div>
                </div>

                <button className="w-full mt-4 btn btn-primary">
                  Start Learning →
                </button>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📚</div>
            <p className="text-gray-600 text-lg">
              {selectedGrade === 'all'
                ? 'No lessons available yet. Check back soon!'
                : `No lessons for Class ${selectedGrade} yet.`}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
