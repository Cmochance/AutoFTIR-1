import { motion } from 'framer-motion'
import Button from '@/components/common/Button'
import Input from '@/components/common/Input'

export default function Settings() {
  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-title text-ink-black mb-6">设置</h1>

        {/* 账户设置 */}
        <div className="ink-card p-6 mb-6">
          <h2 className="font-title text-xl text-ink-black mb-4">账户信息</h2>
          <div className="space-y-4">
            <Input label="邮箱" type="email" placeholder="your@email.com" disabled />
            <Button variant="ghost">修改密码</Button>
          </div>
        </div>

        {/* 分析设置 */}
        <div className="ink-card p-6 mb-6">
          <h2 className="font-title text-xl text-ink-black mb-4">分析偏好</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-ink-medium text-sm mb-2">默认图表样式</label>
              <select className="ink-input">
                <option value="scientific">科研风格</option>
                <option value="publication">期刊级</option>
                <option value="presentation">演示用</option>
              </select>
            </div>
            <div>
              <label className="block text-ink-medium text-sm mb-2">默认导出格式</label>
              <select className="ink-input">
                <option value="png">PNG</option>
                <option value="svg">SVG</option>
                <option value="pdf">PDF</option>
              </select>
            </div>
          </div>
        </div>

        {/* 配额信息 */}
        <div className="ink-card p-6">
          <h2 className="font-title text-xl text-ink-black mb-4">使用配额</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-ink-medium">本月已分析</span>
              <span className="text-ink-black font-mono">0 / 100 次</span>
            </div>
            <div className="w-full h-2 bg-paper-cream rounded-full overflow-hidden">
              <div className="h-full bg-cyan-ink" style={{ width: '0%' }} />
            </div>
            <p className="text-sm text-ink-light">
              配额将于每月 1 日重置
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
