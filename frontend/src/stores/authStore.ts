import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
}

interface AuthState {
  user: User | null
  token: string | null
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      
      login: async (email: string, _password: string) => {
        // TODO: 实现 Supabase Auth
        set({
          user: { id: '1', email },
          token: 'mock-token',
        })
      },
      
      logout: () => {
        set({ user: null, token: null })
      },
    }),
    {
      name: 'scidata-auth',
    }
  )
)
