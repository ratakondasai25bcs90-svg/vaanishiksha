import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Login from './pages/Login'
import Register from './pages/Register'
import TeacherDashboard from './pages/TeacherDashboard'
import StudentDashboard from './pages/StudentDashboard'
import LecturePlayer from './pages/LecturePlayer'

function App() {
  const { user } = useAuthStore()

  return (
    <Routes>
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
      <Route path="/register" element={!user ? <Register /> : <Navigate to="/" />} />
      
      <Route 
        path="/" 
        element={
          user ? (
            user.role === 'teacher' ? <Navigate to="/teacher/dashboard" /> : <Navigate to="/student/dashboard" />
          ) : (
            <Navigate to="/login" />
          )
        } 
      />
      
      <Route 
        path="/teacher/dashboard" 
        element={user?.role === 'teacher' ? <TeacherDashboard /> : <Navigate to="/login" />} 
      />
      
      <Route 
        path="/student/dashboard" 
        element={user?.role === 'student' ? <StudentDashboard /> : <Navigate to="/login" />} 
      />
      
      <Route 
        path="/lecture/:lectureId" 
        element={user ? <LecturePlayer /> : <Navigate to="/login" />} 
      />
    </Routes>
  )
}

export default App
