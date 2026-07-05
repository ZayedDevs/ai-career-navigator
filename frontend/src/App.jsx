import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Upload from './pages/Upload'
import Gap from './pages/Gap'
import Predict from './pages/Predict'
import Roadmap from './pages/Roadmap'
import Dashboard from './pages/Dashboard'
import MyCourses from './pages/MyCourses'
import MyRoadmaps from './pages/MyRoadmaps'
import AskTutor from './pages/AskTutor'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
          <Route path="/gap" element={<ProtectedRoute><Gap /></ProtectedRoute>} />
          <Route path="/predict" element={<ProtectedRoute><Predict /></ProtectedRoute>} />
          <Route path="/roadmap" element={<ProtectedRoute><Roadmap /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/my-learning/courses" element={<ProtectedRoute><MyCourses /></ProtectedRoute>} />
          <Route path="/my-learning/roadmaps" element={<ProtectedRoute><MyRoadmaps /></ProtectedRoute>} />
          <Route path="/ask" element={<ProtectedRoute><AskTutor /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
