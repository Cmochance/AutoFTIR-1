import { motion } from 'framer-motion'

export default function History() {
  // TODO: 从后端获取历史记录
  const histories: any[] = []

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-title text-ink-black mb-6">历史记录</h1>

        {histories.length === 0 ? (
          <div className="ink-card p-12 text-center">
            <div className="text-4xl mb-4">📋</div>
            <p className="text-ink-medium mb-2">暂无分析记录</p>
            <p className="text-sm text-ink-light">
              您的分析记录将在此显示
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {histories.map((item, index) => (
              <motion.div
                key={item.id}
                className="ink-card p-4 flex items-center gap-4 cursor-pointer"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.01 }}
              >
                <div className="w-16 h-16 bg-paper-cream rounded-sm flex items-center justify-center">
                  <span className="text-2xl">📊</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-body text-ink-black">{item.filename}</h3>
                  <p className="text-sm text-ink-light">
                    {item.dataType} · {item.createdAt}
                  </p>
                </div>
                <div className="text-ink-light">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  )
}
