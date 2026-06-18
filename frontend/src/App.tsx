import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import ProfileBuilder from './pages/ProfileBuilder'
import GenerateResume from './pages/GenerateResume'
import Results from './pages/Results'
import History from './pages/History'
import Admin from './pages/Admin'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/profile" element={<ProfileBuilder />} />
        <Route path="/generate" element={<GenerateResume />} />
        <Route path="/results/:versionId" element={<Results />} />
        <Route path="/results" element={<Results />} />
        <Route path="/history" element={<History />} />
        <Route path="/admin" element={<Admin />} />
      </Route>
    </Routes>
  )
}
