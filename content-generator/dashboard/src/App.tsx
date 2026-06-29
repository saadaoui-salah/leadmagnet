import { useState } from 'react'
import { Dashboard } from './components/Dashboard'
import { BufferUpload } from './components/BufferUpload'

type Page = 'dashboard' | 'buffer'

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')

  if (page === 'buffer') {
    return <BufferUpload onBack={() => setPage('dashboard')} />
  }

  return <Dashboard onNavigate={() => setPage('buffer')} />
}
