import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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

export default function TeacherDashboard() {
  const { user, logout } = useAuthStore()
  const queryClient = useQueryClient()
  const [showUpload, setShowUpload] = useState(false)
  const [uploadData, setUploadData] = useState({
    title: '',
    description: '',
    subject: '',
    grade_level: 1,
    original_language: 'en',
  })
  const [file, setFile] = useState<File | null>(null)

  const { data: lectures, isLoading } = useQuery({
    queryKey: ['lectures'],
    queryFn: async () => {
      const response = await api.get<Lecture[]>('/lectures/')
      return response.data
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected')
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', uploadData.title)
      formData.append('description', uploadData.description)
      formData.append('subject', uploadData.subject)
      formData.append('grade_level', uploadData.grade_level.toString())
      formData.append('original_language', uploadData.original_language)

      const response = await api.post('/lectures/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lectures'] })
      setShowUpload(false)
      setFile(null)
      setUploadData({
        title: '',
        description: '',
        subject: '',
        grade_level: 1,
        original_language: 'en',
      })
    },
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary-700">Teacher Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.full_name}</span>
            <button onClick={logout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">My Lectures</h2>
          <button
            onClick={() => setShowUpload(true)}
            className="btn btn-primary"
          >
            + Upload Lecture
          </button>
        </div>

        {showUpload && (
          <div className="card mb-6">
            <h3 className="text-lg font-semibold mb-4">Upload New Lecture</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                uploadMutation.mutate()
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium mb-1">File</label>
                <input
                  type="file"
                  accept="audio/*,video/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <input
                  type="text"
                  value={uploadData.title}
                  onChange={(e) => setUploadData({ ...uploadData, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={uploadData.description}
                  onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Subject</label>
                  <input
                    type="text"
                    value={uploadData.subject}
                    onChange={(e) => setUploadData({ ...uploadData, subject: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Grade</label>
                  <select
                    value={uploadData.grade_level}
                    onChange={(e) => setUploadData({ ...uploadData, grade_level: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((grade) => (
                      <option key={grade} value={grade}>
                        Class {grade}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Language</label>
                  <select
                    value={uploadData.original_language}
                    onChange={(e) => setUploadData({ ...uploadData, original_language: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="ta">Tamil</option>
                    <option value="te">Telugu</option>
                    <option value="kn">Kannada</option>
                    <option value="bn">Bengali</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-2">
                <button type="submit" className="btn btn-primary" disabled={uploadMutation.isPending}>
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowUpload(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {isLoading ? (
          <div className="text-center py-12">Loading...</div>
        ) : lectures && lectures.length > 0 ? (
          <div className="grid gap-4">
            {lectures.map((lecture) => (
              <div key={lecture.id} className="card">
                <div className="flex justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">{lecture.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{lecture.description}</p>
                    <div className="flex gap-4 mt-2 text-sm text-gray-500">
                      <span>Grade {lecture.grade_level}</span>
                      <span>•</span>
                      <span>{lecture.subject}</span>
                      <span>•</span>
                      <span>{lecture.original_language.toUpperCase()}</span>
                    </div>
                  </div>
                  <div className="text-sm">
                    <div className="text-gray-600">Available in:</div>
                    <div className="font-medium">
                      {lecture.available_languages.length > 0
                        ? lecture.available_languages.join(', ').toUpperCase()
                        : 'Original only'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            No lectures uploaded yet. Click "Upload Lecture" to get started!
          </div>
        )}
      </div>
    </div>
  )
}
