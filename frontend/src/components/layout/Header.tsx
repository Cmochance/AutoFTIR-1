import { motion } from 'framer-motion'
import { useAuthStore } from '@/stores/authStore'
import Button from '../common/Button'

interface HeaderProps {
  onMenuClick: () => void
}

export default function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuthStore()

  return (
    <motion.header
      className="h-16 border-b border-paper-aged bg-paper-white/80 backdrop-blur-sm flex items-center justify-between px-6 flex-shrink-0"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* 左侧 */}
      <div className="flex items-center gap-4">
        <button
          className="p-2 hover:bg-paper-cream rounded-sm transition-colors"
          onClick={onMenuClick}
        >
          <svg className="w-6 h-6 text-ink-medium" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {/* 右侧 */}
      <div className="flex items-center gap-4">
        {user ? (
          <div className="flex items-center gap-3">
            <span className="text-ink-medium font-body">{user.email}</span>
            <Button variant="ghost" size="sm" onClick={logout}>
              退出
            </Button>
          </div>
        ) : (
          <Button variant="ink" size="sm">
            登录
          </Button>
        )}
      </div>
    </motion.header>
  )
}
