import { create } from 'zustand'

export type AnalyzeStatus = 'idle' | 'uploading' | 'processing' | 'rendering' | 'analyzing' | 'done' | 'error'

interface AnalyzeState {
  // 状态
  status: AnalyzeStatus
  progress: number
  error: string | null
  
  // 数据
  file: File | null
  processedData: any | null
  chartImage: string | null
  chartMetadata: any | null
  report: string | null
  
  // 操作
  setFile: (file: File | null) => void
  setStatus: (status: AnalyzeStatus) => void
  setProgress: (progress: number) => void
  setError: (error: string | null) => void
  setProcessedData: (data: any) => void
  setChartImage: (image: string | null) => void
  setChartMetadata: (metadata: any) => void
  setReport: (report: string | null) => void
  reset: () => void
}

const initialState = {
  status: 'idle' as AnalyzeStatus,
  progress: 0,
  error: null,
  file: null,
  processedData: null,
  chartImage: null,
  chartMetadata: null,
  report: null,
}

export const useAnalyzeStore = create<AnalyzeState>((set) => ({
  ...initialState,
  
  setFile: (file) => set({ file }),
  setStatus: (status) => set({ status }),
  setProgress: (progress) => set({ progress }),
  setError: (error) => set({ error, status: error ? 'error' : 'idle' }),
  setProcessedData: (processedData) => set({ processedData }),
  setChartImage: (chartImage) => set({ chartImage }),
  setChartMetadata: (chartMetadata) => set({ chartMetadata }),
  setReport: (report) => set({ report }),
  reset: () => set(initialState),
}))
