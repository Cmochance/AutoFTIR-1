import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import Button from '@/components/common/Button'

export default function Welcome() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* 标题 */}
        <h1 className="text-6xl font-title text-ink-black mb-4">墨研</h1>
        <p className="text-xl text-ink-medium mb-2">SciData - 科研数据分析平台</p>
        <p className="text-ink-light mb-8 max-w-md mx-auto">
          上传您的科研数据，AI 自动识别类型、绑制图表、深度分析
        </p>

        {/* 功能卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 max-w-3xl mx-auto">
          <motion.div
            className="ink-card p-6"
            whileHover={{ y: -4 }}
            transition={{ duration: 0.2 }}
          >
            <div className="text-3xl mb-3">📊</div>
            <h3 className="font-title text-lg text-ink-black mb-2">智能识别</h3>
            <p className="text-sm text-ink-light">
              自动识别 FTIR、XRD、SEM 等多种科研数据类型
            </p>
          </motion.div>

          <motion.div
            className="ink-card p-6"
            whileHover={{ y: -4 }}
            transition={{ duration: 0.2 }}
          >
            <div className="text-3xl mb-3">🎨</div>
            <h3 className="font-title text-lg text-ink-black mb-2">美观图表</h3>
            <p className="text-sm text-ink-light">
              生成期刊级科研图表，支持多种样式和格式导出
            </p>
          </motion.div>

          <motion.div
            className="ink-card p-6"
            whileHover={{ y: -4 }}
            transition={{ duration: 0.2 }}
          >
            <div className="text-3xl mb-3">🤖</div>
            <h3 className="font-title text-lg text-ink-black mb-2">AI 分析</h3>
            <p className="text-sm text-ink-light">
              结合最新文献和知识库，提供专业深度分析
            </p>
          </motion.div>
        </div>

        {/* 开始按钮 */}
        <Button
          variant="seal"
          size="lg"
          onClick={() => navigate('/analyze')}
        >
          开始分析
        </Button>
      </motion.div>
    </div>
  )
}
