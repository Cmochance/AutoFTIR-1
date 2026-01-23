import { Outlet } from 'react-router-dom'
import { useState } from 'react'
import { motion } from 'framer-motion'
import Sidebar from './Sidebar'
import Header from './Header'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="h-screen flex bg-paper-gradient overflow-hidden">
      {/* 侧边栏 */}
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col min-w-0 min-h-0 max-h-full overflow-hidden">
        {/* 头部 */}
        <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

        {/* 页面内容 */}
        <motion.div
          className="flex-1 overflow-auto p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}
