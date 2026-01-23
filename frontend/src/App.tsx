import { Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import Layout from './components/layout/Layout'
import Welcome from './pages/Welcome'
import Analyze from './pages/Analyze'
import History from './pages/History'
import Settings from './pages/Settings'

function App() {
  return (
    <motion.div
      className="h-screen bg-paper-gradient"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Welcome />} />
          <Route path="analyze" element={<Analyze />} />
          <Route path="history" element={<History />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </motion.div>
  )
}

export default App
