import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import { useAnalyzeStore } from '@/stores/analyzeStore'
import Button from '@/components/common/Button'
import Loading from '@/components/common/Loading'

export default function Analyze() {
  const {
    status,
    file,
    chartImage,
    report,
    setFile,
    setStatus,
    reset,
  } = useAnalyzeStore()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [setFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
  })

  const handleAnalyze = async () => {
    if (!file) return

    setStatus('processing')
    
    // TODO: 调用后端 API
    // 模拟分析过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    setStatus('done')
  }

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-title text-ink-black mb-6">数据分析</h1>

        {/* 文件上传区域 */}
        {status === 'idle' && (
          <div
            {...getRootProps()}
            className={`upload-zone text-center ${isDragActive ? 'active' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="text-4xl mb-4">📁</div>
            {isDragActive ? (
              <p className="text-ink-medium">释放文件以上传...</p>
            ) : (
              <>
                <p className="text-ink-medium mb-2">拖拽文件到此处，或点击选择</p>
                <p className="text-sm text-ink-light">
                  支持 CSV、TXT、Excel 格式
                </p>
              </>
            )}
          </div>
        )}

        {/* 已选择文件 */}
        {file && status === 'idle' && (
          <motion.div
            className="mt-6 ink-card p-6"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-3xl">📄</div>
                <div>
                  <p className="font-body text-ink-black">{file.name}</p>
                  <p className="text-sm text-ink-light">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <Button variant="ghost" onClick={reset}>
                  重选
                </Button>
                <Button variant="seal" onClick={handleAnalyze}>
                  开始分析
                </Button>
              </div>
            </div>
          </motion.div>
        )}

        {/* 分析中 */}
        {(status === 'processing' || status === 'rendering' || status === 'analyzing') && (
          <motion.div
            className="mt-6 ink-card p-12 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Loading size="lg" text="正在分析数据..." />
            <div className="mt-6 text-sm text-ink-light">
              {status === 'processing' && '识别数据类型中...'}
              {status === 'rendering' && '绑制图表中...'}
              {status === 'analyzing' && 'AI 深度分析中...'}
            </div>
          </motion.div>
        )}

        {/* 分析结果 */}
        {status === 'done' && (
          <motion.div
            className="mt-6 space-y-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* 图表 */}
            <div className="ink-card p-6">
              <h2 className="font-title text-xl text-ink-black mb-4">生成图表</h2>
              <div className="bg-paper-cream p-4 rounded-sm flex items-center justify-center min-h-[300px]">
                {chartImage ? (
                  <img src={chartImage} alt="分析结果图表" className="max-w-full" />
                ) : (
                  <p className="text-ink-light">图表预览区域</p>
                )}
              </div>
              <div className="flex gap-3 mt-4">
                <Button variant="ghost" size="sm">下载 PNG</Button>
                <Button variant="ghost" size="sm">下载 SVG</Button>
                <Button variant="ghost" size="sm">下载 PDF</Button>
              </div>
            </div>

            {/* AI 分析报告 */}
            <div className="result-card">
              <h2 className="font-title text-xl text-ink-black mb-4">AI 分析报告</h2>
              <div className="markdown-content">
                {report || (
                  <p className="text-ink-light">
                    AI 分析报告将在此显示，包含数据解读、峰归属、物质推断等专业分析。
                  </p>
                )}
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-4">
              <Button variant="ink" onClick={reset}>
                分析新数据
              </Button>
              <Button variant="ghost">
                保存到历史
              </Button>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
