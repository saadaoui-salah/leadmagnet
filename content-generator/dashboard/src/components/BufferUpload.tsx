import { useState, useEffect, useCallback } from 'react'
import { Upload, CheckCircle2, XCircle, Loader2, ExternalLink, ArrowLeft, Settings, Send, FileText, Image as ImageIcon, Trash2, FolderIcon, RefreshCw } from 'lucide-react'
import { slides } from '../data/mockData'

interface Channel {
  id: string
  service: string
  name: string
}

interface UploadedFile {
  name: string
  id?: string
  link?: string
  error?: string
}

interface Config {
  bufferApiKey: string | null
  hasGoogleDrive: boolean
  googleDriveFolderId: string | null
}

interface Notification {
  id: number
  type: 'success' | 'error' | 'info' | 'progress'
  message: string
  progress?: number
}

let notifId = 0

export function BufferUpload({ onBack }: { onBack: () => void }) {
  const [config, setConfig] = useState<Config | null>(null)
  const [channels, setChannels] = useState<Channel[]>([])
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null)
  const [selectedSlides, setSelectedSlides] = useState<Set<number>>(new Set())
  const [caption, setCaption] = useState('')
  const [postTitle, setPostTitle] = useState('')
  const [schedulingType, setSchedulingType] = useState<'automatic' | 'custom'>('automatic')
  const [customTime, setCustomTime] = useState('')
  const [savingAsDraft, setSavingAsDraft] = useState(false)

  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState('')
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])

  const [posting, setPosting] = useState(false)
  const [postResult, setPostResult] = useState<any>(null)

  const [generatingCaption, setGeneratingCaption] = useState(false)

  const [showSettings, setShowSettings] = useState(false)
  const [bufferKeyInput, setBufferKeyInput] = useState('')
  const [driveCredsInput, setDriveCredsInput] = useState('')
  const [driveFolderInput, setDriveFolderInput] = useState('')
  const [savingConfig, setSavingConfig] = useState(false)

  const [filter, setFilter] = useState<'all' | 'linkedin' | 'instagram'>('all')

  const [driveAuth, setDriveAuth] = useState<{ hasToken: boolean; isValid: boolean } | null>(null)

  const [driveFiles, setDriveFiles] = useState<{ id: string; name: string; mimeType: string; size?: string; modifiedTime?: string }[]>([])
  const [driveFolders, setDriveFolders] = useState<{ id: string; name: string }[]>([])
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null)
  const [_parentFolderId, setParentFolderId] = useState<string | null>(null)
  const [_rootFolderId, setRootFolderId] = useState<string | null>(null)
  const [folderPath, setFolderPath] = useState<{ id: string; name: string }[]>([])
  const [selectedDriveFiles, setSelectedDriveFiles] = useState<Set<string>>(new Set())
  const [loadingDriveFiles, setLoadingDriveFiles] = useState(false)
  const [deletingFile, setDeletingFile] = useState<string | null>(null)

  const [notifications, setNotifications] = useState<Notification[]>([])

  const addNotification = useCallback((type: Notification['type'], message: string, progress?: number) => {
    const id = ++notifId
    setNotifications(prev => [...prev, { id, type, message, progress }])
    return id
  }, [])

  const updateNotification = useCallback((id: number, updates: Partial<Notification>) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, ...updates } : n))
  }, [])

  const removeNotification = useCallback((id: number) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const loadConfig = useCallback(async () => {
    try {
      const res = await fetch('/api/config')
      const data = await res.json()
      setConfig(data)
      if (!data.bufferApiKey || !data.hasGoogleDrive) {
        setShowSettings(true)
      }
    } catch {}
  }, [])

  const loadChannels = useCallback(async () => {
    try {
      const res = await fetch('/api/buffer/channels')
      const data = await res.json()
      if (data.ok) {
        setChannels(data.channels)
        if (data.needsRefresh) {
          // Auto-refresh on first load if no cached channels
          refreshChannels()
        }
      }
    } catch {}
  }, [])

  const [refreshingChannels, setRefreshingChannels] = useState(false)

  const refreshChannels = useCallback(async () => {
    setRefreshingChannels(true)
    try {
      const res = await fetch('/api/buffer/channels/refresh')
      const data = await res.json()
      if (data.ok) {
        setChannels(data.channels)
      } else if (data.error) {
        addNotification('error', `Failed to refresh channels: ${data.error}`)
      }
    } catch (err: any) {
      addNotification('error', `Failed to refresh channels: ${err.message}`)
    }
    setRefreshingChannels(false)
  }, [addNotification])

  const checkDriveAuth = useCallback(async () => {
    try {
      const res = await fetch('/api/drive/status')
      const data = await res.json()
      setDriveAuth({ hasToken: data.hasToken, isValid: data.isValid })
    } catch {}
  }, [])

  useEffect(() => {
    loadConfig()
    loadChannels()
    checkDriveAuth()

    // Listen for auth success from popup tab
    const handleMessage = (e: MessageEvent) => {
      if (e.data?.type === 'drive-auth' && e.data?.success) {
        checkDriveAuth()
        addNotification('success', 'Google Drive connected successfully!')
      }
    }
    window.addEventListener('message', handleMessage)

    return () => window.removeEventListener('message', handleMessage)
  }, [loadConfig, loadChannels, checkDriveAuth, addNotification])

  const handleDriveAuth = async () => {
    try {
      const res = await fetch('/api/drive/auth-url')
      const data = await res.json()
      if (data.ok) {
        window.open(data.url, '_blank')
      }
    } catch {}
  }

  const handleDriveDisconnect = async () => {
    try {
      await fetch('/api/drive/disconnect', { method: 'POST' })
      setDriveAuth(null)
      setDriveFiles([])
    } catch {}
  }

  const loadDriveFiles = useCallback(async (folderId?: string) => {
    setLoadingDriveFiles(true)
    try {
      const url = folderId ? `/api/drive/files?folderId=${folderId}` : '/api/drive/files'
      const res = await fetch(url)
      const data = await res.json()
      if (data.ok) {
        setDriveFiles(data.files)
        setDriveFolders(data.folders)
        setCurrentFolderId(data.folderId)
        setParentFolderId(data.parentFolderId)
        setRootFolderId(data.rootFolderId)
      }
    } catch {}
    setLoadingDriveFiles(false)
  }, [])

  useEffect(() => {
    if (driveAuth?.isValid) {
      loadDriveFiles()
    }
  }, [driveAuth, loadDriveFiles])

  const navigateToFolder = (folderId: string, folderName: string) => {
    setSelectedDriveFiles(new Set())
    setFolderPath(prev => [...prev, { id: folderId, name: folderName }])
    loadDriveFiles(folderId)
  }

  const navigateToBreadcrumb = (index: number) => {
    setSelectedDriveFiles(new Set())
    if (index < 0) {
      // Go to root
      setFolderPath([])
      loadDriveFiles()
    } else {
      const target = folderPath[index]
      setFolderPath(prev => prev.slice(0, index + 1))
      loadDriveFiles(target.id)
    }
  }

  const deleteDriveFile = async (fileId: string, fileName: string) => {
    if (!confirm(`Delete "${fileName}" from Google Drive?`)) return
    setDeletingFile(fileId)
    const notifId = addNotification('info', `Deleting ${fileName}...`)
    try {
      const res = await fetch('/api/drive/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileId }),
      })
      const data = await res.json()
      if (data.ok) {
        setDriveFiles(prev => prev.filter(f => f.id !== fileId))
        updateNotification(notifId, { message: `Deleted ${fileName}`, type: 'success', progress: 100 })
        setTimeout(() => removeNotification(notifId), 3000)
      } else {
        updateNotification(notifId, { message: `Delete failed: ${data.error}`, type: 'error' })
      }
    } catch (err: any) {
      updateNotification(notifId, { message: `Delete failed: ${err.message}`, type: 'error' })
    }
    setDeletingFile(null)
  }

  const toggleDriveFile = (fileId: string) => {
    setSelectedDriveFiles(prev => {
      const next = new Set(prev)
      if (next.has(fileId)) next.delete(fileId)
      else next.add(fileId)
      return next
    })
  }

  const selectAllDriveFiles = () => {
    if (selectedDriveFiles.size === driveFiles.length) {
      setSelectedDriveFiles(new Set())
    } else {
      setSelectedDriveFiles(new Set(driveFiles.map(f => f.id)))
    }
  }

  const handleScheduleDriveFiles = async () => {
    if (selectedDriveFiles.size === 0 || !selectedChannel) return

    const selected = driveFiles.filter(f => selectedDriveFiles.has(f.id))
    // Build assets with proper type detection
    const assets = selected.map(f => {
      const isPdf = f.name.endsWith('.pdf') || f.mimeType === 'application/pdf'
      return {
        url: `https://drive.google.com/uc?export=view&id=${f.id}`,
        type: isPdf ? 'document' : 'image',
        title: postTitle || f.name.replace(/\.[^.]+$/, ''),
        thumbnailUrl: `https://drive.google.com/uc?export=view&id=${f.id}`,
      }
    })

    console.log('Scheduling:', { channelId: selectedChannel, caption, assets, schedulingType })

    setPosting(true)
    setPostResult(null)

    const notifId = addNotification('info', `Scheduling ${selected.length} file(s) to Buffer...`)

    try {
      const body: any = {
        channelId: selectedChannel,
        text: caption,
        assets,
        schedulingType,
        mode: savingAsDraft ? 'addToQueue' : schedulingType === 'custom' ? 'custom' : 'addToQueue',
      }

      if (savingAsDraft) body.saveToDraft = true
      if (schedulingType === 'custom' && customTime) body.dueAt = new Date(customTime).toISOString()

      updateNotification(notifId, { message: 'Creating post...', type: 'progress', progress: 50 })

      const res = await fetch('/api/buffer/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      console.log('Post response:', data)
      setPostResult(data)

      if (data.data?.createPost?.post) {
        updateNotification(notifId, { message: 'Post created successfully!', type: 'success', progress: 100 })
        setTimeout(() => removeNotification(notifId), 3000)
        setSelectedDriveFiles(new Set())
      } else {
        const errMsg = data.error || data.data?.createPost?.message || data.errors?.[0]?.message || 'Unknown error'
        updateNotification(notifId, { message: `Post failed: ${errMsg}`, type: 'error' })
      }
    } catch (err: any) {
      console.error('Schedule error:', err)
      updateNotification(notifId, { message: `Post failed: ${err.message}`, type: 'error' })
    } finally {
      setPosting(false)
    }
  }

  const deleteSelectedDriveFiles = async () => {
    if (selectedDriveFiles.size === 0) return
    if (!confirm(`Delete ${selectedDriveFiles.size} file(s) from Google Drive?`)) return

    const notifId = addNotification('info', `Deleting ${selectedDriveFiles.size} file(s)...`)
    let deleted = 0
    let failed = 0

    for (const fileId of selectedDriveFiles) {
      try {
        const res = await fetch('/api/drive/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fileId }),
        })
        const data = await res.json()
        if (data.ok) deleted++
        else failed++
      } catch {
        failed++
      }
    }

    setDriveFiles(prev => prev.filter(f => !selectedDriveFiles.has(f.id)))
    setSelectedDriveFiles(new Set())

    if (failed === 0) {
      updateNotification(notifId, { message: `Deleted ${deleted} file(s)`, type: 'success', progress: 100 })
    } else {
      updateNotification(notifId, { message: `Deleted ${deleted}, failed ${failed}`, type: failed > 0 ? 'error' : 'success', progress: 100 })
    }
    setTimeout(() => removeNotification(notifId), 3000)
  }

  const handleGenerateCaption = async () => {
    setGeneratingCaption(true)
    try {
      const platform = selectedSlides.size > 0
        ? slides.find(s => selectedSlides.has(s.id))?.platform || 'linkedin'
        : 'linkedin'

      const res = await fetch('/api/generate-caption', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, slideCount: selectedSlides.size }),
      })
      const data = await res.json()
      if (data.ok) {
        if (platform === 'youtube') {
          // YouTube returns title + description separated by blank line
          const parts = data.caption.split('\n\n')
          if (parts.length >= 2) {
            setPostTitle(parts[0].trim())
            setCaption(parts.slice(1).join('\n\n').trim())
          } else {
            setCaption(data.caption)
          }
        } else if (platform === 'linkedin' && data.title) {
          // LinkedIn returns title + caption
          setPostTitle(data.title)
          setCaption(data.caption)
        } else {
          setCaption(data.caption)
          setPostTitle('')
        }
      } else {
        setCaption(`Error: ${data.error}`)
      }
    } catch (err: any) {
      setCaption(`Error: ${err.message}`)
    } finally {
      setGeneratingCaption(false)
    }
  }

  const handleSaveConfig = async () => {
    setSavingConfig(true)
    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bufferApiKey: bufferKeyInput || undefined,
          googleDriveCredentials: driveCredsInput || undefined,
          googleDriveFolderId: driveFolderInput || undefined,
        }),
      })
      await loadConfig()
      await loadChannels()
      setShowSettings(false)
    } finally {
      setSavingConfig(false)
    }
  }

  const toggleSlide = (id: number) => {
    setSelectedSlides(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = (platform: 'all' | 'linkedin' | 'instagram') => {
    const filtered = platform === 'all' ? slides : slides.filter(s => s.platform === platform)
    setSelectedSlides(new Set(filtered.map(s => s.id)))
  }

  const handleUpload = async () => {
    if (selectedSlides.size === 0) return
    setUploading(true)
    setUploadProgress('Starting upload...')
    setUploadedFiles([])

    const selectedSlidesArray = slides.filter(s => selectedSlides.has(s.id))
    const selectedPlatform = selectedSlidesArray[0]?.platform || 'linkedin'
    const notifId = addNotification('info', `Uploading ${selectedPlatform} carousel to Google Drive...`)

    try {
      const filesToSend = selectedSlidesArray.map(s => ({
        path: s.file.startsWith('/') ? s.file.slice(1) : s.file,
        name: s.isPdf ? `${s.title.replace(/\s+/g, '-')}_${s.platform}.pdf` : `${s.id}_${s.platform}.png`,
        mimeType: s.isPdf ? 'application/pdf' : 'image/png',
      }))

      updateNotification(notifId, { message: `Uploading ${filesToSend.length} file(s)...`, type: 'progress', progress: 20 })
      setUploadProgress(`Uploading to Google Drive...`)

      const res = await fetch('/api/drive/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: filesToSend, platform: selectedPlatform }),
      })
      const data = await res.json()

      if (data.ok) {
        setUploadedFiles(data.files)
        updateNotification(notifId, { message: `Uploaded ${data.files.length} slides to Google Drive!`, type: 'success', progress: 100 })
        setUploadProgress('Upload complete!')
        setTimeout(() => removeNotification(notifId), 3000)
      } else {
        updateNotification(notifId, { message: `Upload failed: ${data.error}`, type: 'error' })
        setUploadProgress(`Error: ${data.error}`)
      }
    } catch (err: any) {
      updateNotification(notifId, { message: `Upload failed: ${err.message}`, type: 'error' })
      setUploadProgress(`Error: ${err.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handlePost = async () => {
    const successfulUploads = uploadedFiles.filter(f => f.link)
    if (!selectedChannel || successfulUploads.length === 0) return

    setPosting(true)
    setPostResult(null)

    const notifId = addNotification('info', 'Posting to Buffer...')

    try {
      const body: any = {
        channelId: selectedChannel,
        text: caption,
        assets: successfulUploads.map(f => ({
          url: f.link,
          type: 'image',
        })),
        schedulingType,
        mode: savingAsDraft ? 'addToQueue' : schedulingType === 'custom' ? 'custom' : 'addToQueue',
      }

      if (savingAsDraft) body.saveToDraft = true
      if (schedulingType === 'custom' && customTime) body.dueAt = new Date(customTime).toISOString()

      updateNotification(notifId, { message: 'Creating post...', type: 'progress', progress: 50 })

      const res = await fetch('/api/buffer/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      setPostResult(data)

      if (data.data?.createPost?.post) {
        updateNotification(notifId, { message: 'Post created successfully!', type: 'success', progress: 100 })
        setTimeout(() => removeNotification(notifId), 3000)
      } else {
        updateNotification(notifId, { message: `Post failed: ${data.data?.createPost?.message || data.error || 'Unknown error'}`, type: 'error' })
      }
    } catch (err: any) {
      setPostResult({ error: err.message })
      updateNotification(notifId, { message: `Post failed: ${err.message}`, type: 'error' })
    } finally {
      setPosting(false)
    }
  }

  const filteredSlides = filter === 'all' ? slides : slides.filter(s => s.platform === filter)
  const selectedCount = selectedSlides.size
  const uploadCount = uploadedFiles.filter(f => f.link).length

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header
        className="sticky top-0 z-40 bg-bg/80 backdrop-blur-xl border-b border-border/50"
        style={{ paddingLeft: 48, paddingRight: 48 }}
      >
        <div
          className="flex items-center justify-between"
          style={{ maxWidth: 1400, margin: '0 auto', height: 56 }}
        >
          <div className="flex items-center" style={{ gap: 12 }}>
            <button
              onClick={onBack}
              className="flex items-center justify-center rounded-lg"
              style={{ padding: '6px 8px', color: '#94a3b8', cursor: 'pointer', background: 'none', border: 'none' }}
            >
              <ArrowLeft size={18} />
            </button>
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)' }}>
              <Send className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-lg font-bold">Buffer Upload</h1>
          </div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2 rounded-lg"
            style={{ padding: '6px 12px', fontSize: 13, background: '#1e293b', color: '#94a3b8', border: '1px solid rgba(148,163,184,0.2)', cursor: 'pointer' }}
          >
            <Settings size={14} />
            Settings
          </button>
        </div>
      </header>

      {/* Notifications */}
      <div style={{ position: 'fixed', top: 70, right: 20, zIndex: 1000, display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 360 }}>
        {notifications.map(notif => (
          <div
            key={notif.id}
            className="flex items-center gap-3"
            style={{
              padding: '12px 16px', borderRadius: 10, fontSize: 13, fontWeight: 500,
              background: notif.type === 'success' ? 'rgba(34,197,94,0.15)' : notif.type === 'error' ? 'rgba(239,68,68,0.15)' : notif.type === 'progress' ? 'rgba(99,102,241,0.15)' : 'rgba(148,163,184,0.15)',
              border: `1px solid ${notif.type === 'success' ? 'rgba(34,197,94,0.3)' : notif.type === 'error' ? 'rgba(239,68,68,0.3)' : notif.type === 'progress' ? 'rgba(99,102,241,0.3)' : 'rgba(148,163,184,0.3)'}`,
              color: notif.type === 'success' ? '#22c55e' : notif.type === 'error' ? '#ef4444' : notif.type === 'progress' ? '#818cf8' : '#94a3b8',
              backdropFilter: 'blur(12px)',
            }}
          >
            {notif.type === 'success' ? <CheckCircle2 size={16} /> : notif.type === 'error' ? <XCircle size={16} /> : <Loader2 size={16} className="animate-spin" />}
            <span style={{ flex: 1 }}>{notif.message}</span>
            {notif.type !== 'progress' && (
              <button onClick={() => removeNotification(notif.id)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0 }}>
                <XCircle size={14} />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Settings panel */}
      {showSettings && (
        <div style={{ background: '#0f172a', borderBottom: '1px solid rgba(99,102,241,0.2)', padding: '20px 48px' }}>
          <div style={{ maxWidth: 1400, margin: '0 auto' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0', marginBottom: 16 }}>API Configuration</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>Buffer API Key</label>
                <input
                  type="password"
                  value={bufferKeyInput}
                  onChange={e => setBufferKeyInput(e.target.value)}
                  placeholder={config?.bufferApiKey || 'Enter Buffer API key'}
                  style={{ width: '100%', padding: '8px 12px', fontSize: 13, background: '#1e293b', border: '1px solid rgba(148,163,184,0.2)', borderRadius: 8, color: '#e2e8f0', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>Google Drive Credentials (JSON)</label>
                <input
                  type="password"
                  value={driveCredsInput}
                  onChange={e => setDriveCredsInput(e.target.value)}
                  placeholder={config?.hasGoogleDrive ? '•••• configured' : 'Paste service account JSON'}
                  style={{ width: '100%', padding: '8px 12px', fontSize: 13, background: '#1e293b', border: '1px solid rgba(148,163,184,0.2)', borderRadius: 8, color: '#e2e8f0', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>Drive Folder ID (optional)</label>
                <input
                  type="text"
                  value={driveFolderInput}
                  onChange={e => setDriveFolderInput(e.target.value)}
                  placeholder={config?.googleDriveFolderId || 'Optional folder ID'}
                  style={{ width: '100%', padding: '8px 12px', fontSize: 13, background: '#1e293b', border: '1px solid rgba(148,163,184,0.2)', borderRadius: 8, color: '#e2e8f0', outline: 'none' }}
                />
              </div>
            </div>
            <button
              onClick={handleSaveConfig}
              disabled={savingConfig}
              className="flex items-center gap-2 rounded-lg font-semibold"
              style={{ marginTop: 12, padding: '8px 20px', fontSize: 13, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff', border: 'none', cursor: 'pointer' }}
            >
              {savingConfig ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
              Save Configuration
            </button>

            {/* Drive Auth Status */}
            {config?.hasGoogleDrive && (
              <div className="flex items-center" style={{ marginTop: 12, gap: 12 }}>
                {driveAuth?.isValid ? (
                  <>
                    <div className="flex items-center" style={{ gap: 6, padding: '6px 12px', background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 8 }}>
                      <CheckCircle2 size={14} style={{ color: '#22c55e' }} />
                      <span style={{ fontSize: 12, color: '#22c55e' }}>Drive Connected</span>
                    </div>
                    <button
                      onClick={handleDriveDisconnect}
                      style={{ padding: '6px 12px', fontSize: 12, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#ef4444', cursor: 'pointer' }}
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={handleDriveAuth}
                    className="flex items-center gap-2"
                    style={{ padding: '6px 12px', fontSize: 12, background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 8, color: '#f59e0b', cursor: 'pointer' }}
                  >
                    <ExternalLink size={12} />
                    Authorize Google Drive
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main content */}
      <div style={{ paddingLeft: 48, paddingRight: 48 }}>
        <main style={{ maxWidth: 1400, margin: '0 auto', paddingBottom: 60, paddingTop: 32 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 32 }}>

            {/* Left: Slide selection */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <h2 style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Select Slides ({selectedCount})
                </h2>
                <div className="flex items-center" style={{ gap: 8 }}>
                  {(['all', 'linkedin', 'instagram'] as const).map(p => (
                    <button
                      key={p}
                      onClick={() => selectAll(p)}
                      style={{
                        padding: '4px 12px', fontSize: 12, borderRadius: 6, cursor: 'pointer',
                        background: 'none', border: '1px solid rgba(148,163,184,0.2)', color: '#94a3b8',
                      }}
                    >
                      {p === 'all' ? 'All' : p === 'linkedin' ? 'LinkedIn' : 'Instagram'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Platform filter */}
              <div className="flex" style={{ gap: 6, marginBottom: 16 }}>
                {(['all', 'linkedin', 'instagram'] as const).map(p => (
                  <button
                    key={p}
                    onClick={() => setFilter(p)}
                    style={{
                      padding: '6px 14px', fontSize: 12, borderRadius: 8, cursor: 'pointer', fontWeight: 600,
                      background: filter === p ? 'rgba(99,102,241,0.15)' : '#1e293b',
                      color: filter === p ? '#818cf8' : '#64748b',
                      border: filter === p ? '1px solid rgba(99,102,241,0.3)' : '1px solid rgba(148,163,184,0.1)',
                    }}
                  >
                    {p === 'all' ? 'All' : p === 'linkedin' ? 'LinkedIn' : 'Instagram'}
                  </button>
                ))}
              </div>

              {/* Slides grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
                {filteredSlides.map(slide => {
                  const isSelected = selectedSlides.has(slide.id)
                  return (
                    <button
                      key={slide.id}
                      onClick={() => toggleSlide(slide.id)}
                      style={{
                        position: 'relative', borderRadius: 10, overflow: 'hidden', cursor: 'pointer',
                        border: isSelected ? '2px solid #6366f1' : '2px solid transparent',
                        opacity: isSelected ? 1 : 0.6, transition: 'all 0.15s',
                        background: '#0f172a', padding: 0,
                      }}
                    >
                      {slide.isPdf ? (
                        <div style={{
                          width: '100%', aspectRatio: '4/5', display: 'flex', flexDirection: 'column',
                          alignItems: 'center', justifyContent: 'center', gap: 8, background: '#1e293b',
                        }}>
                          <FileText size={32} style={{ color: '#f59e0b' }} />
                          <span style={{ fontSize: 11, color: '#94a3b8', textAlign: 'center', padding: '0 8px' }}>
                            PDF Carousel
                          </span>
                        </div>
                      ) : (
                        <img
                          src={slide.file}
                          alt={slide.title}
                          style={{ width: '100%', aspectRatio: '4/5', objectFit: 'cover', display: 'block' }}
                          loading="lazy"
                        />
                      )}
                      {isSelected && (
                        <div
                          style={{
                            position: 'absolute', top: 6, right: 6, width: 20, height: 20,
                            borderRadius: 10, background: '#6366f1', display: 'flex',
                            alignItems: 'center', justifyContent: 'center',
                          }}
                        >
                          <CheckCircle2 size={12} color="#fff" />
                        </div>
                      )}
                      <div
                        style={{
                          position: 'absolute', bottom: 0, left: 0, right: 0, padding: '4px 6px',
                          background: 'rgba(0,0,0,0.7)', fontSize: 10, color: '#94a3b8', textAlign: 'center',
                        }}
                      >
                        {slide.isPdf ? 'PDF' : slide.platform === 'linkedin' ? 'Li' : 'Ig'} #{slide.id}
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Right: Config & actions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Channel selection */}
              <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid rgba(148,163,184,0.1)', padding: 20 }}>
                <div className="flex items-center justify-between" style={{ marginBottom: 12 }}>
                  <h3 style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>Channel</h3>
                  <button
                    onClick={refreshChannels}
                    disabled={refreshingChannels}
                    className="flex items-center gap-1"
                    style={{ fontSize: 11, color: '#818cf8', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                  >
                    {refreshingChannels ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <RefreshCw size={12} />
                    )}
                    {refreshingChannels ? 'Loading...' : 'Refresh'}
                  </button>
                </div>
                {channels.length === 0 ? (
                  <p style={{ fontSize: 12, color: '#64748b' }}>No channels found. Click Refresh or check your Buffer API key.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {channels.map(ch => (
                      <button
                        key={ch.id}
                        onClick={() => setSelectedChannel(ch.id)}
                        className="flex items-center"
                        style={{
                          gap: 10, padding: '10px 12px', borderRadius: 8, cursor: 'pointer', textAlign: 'left',
                          background: selectedChannel === ch.id ? 'rgba(99,102,241,0.1)' : '#1e293b',
                          border: selectedChannel === ch.id ? '1px solid rgba(99,102,241,0.3)' : '1px solid rgba(148,163,184,0.1)',
                        }}
                      >
                        <div>
                          <div style={{ fontSize: 13, color: '#e2e8f0', fontWeight: 500 }}>{ch.name}</div>
                          <div style={{ fontSize: 11, color: '#64748b' }}>{ch.service} • {ch.id.slice(0, 12)}...</div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Caption */}
              <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid rgba(148,163,184,0.1)', padding: 20 }}>
                <div className="flex items-center justify-between" style={{ marginBottom: 12 }}>
                  <div className="flex items-center" style={{ gap: 8 }}>
                    <h3 style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>
                      {selectedSlides.size > 0 && slides.find(s => selectedSlides.has(s.id))?.platform === 'youtube' ? 'Title & Description' : 'Caption'}
                    </h3>
                    <span
                      style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
                        background: selectedSlides.size > 0 && slides.find(s => selectedSlides.has(s.id))?.platform === 'instagram'
                          ? 'rgba(225,74,149,0.15)'
                          : selectedSlides.size > 0 && slides.find(s => selectedSlides.has(s.id))?.platform === 'youtube'
                            ? 'rgba(255,0,0,0.15)'
                            : 'rgba(10,102,194,0.15)',
                        color: selectedSlides.size > 0 && slides.find(s => selectedSlides.has(s.id))?.platform === 'instagram'
                          ? '#e14a95'
                          : selectedSlides.size > 0 && slides.find(s => selectedSlides.has(s.id))?.platform === 'youtube'
                            ? '#ff0000'
                            : '#0a66c2',
                        border: selectedSlides.size > 0 && slides.find(s => selectedSlides.has(s.id))?.platform === 'instagram'
                          ? '1px solid rgba(225,74,149,0.3)'
                          : selectedSlides.size > 0 && slides.find(s => selectedSlides.has(s.id))?.platform === 'youtube'
                            ? '1px solid rgba(255,0,0,0.3)'
                            : '1px solid rgba(10,102,194,0.3)',
                      }}
                    >
                      {selectedSlides.size > 0
                        ? (slides.find(s => selectedSlides.has(s.id))?.platform || 'linkedin')
                        : 'linkedin'}
                    </span>
                  </div>
                  <button
                    onClick={handleGenerateCaption}
                    disabled={generatingCaption}
                    className="flex items-center gap-2 rounded-lg font-semibold"
                    style={{
                      padding: '5px 12px', fontSize: 11, cursor: generatingCaption ? 'not-allowed' : 'pointer',
                      background: generatingCaption ? '#1e293b' : 'linear-gradient(135deg, #f59e0b, #d97706)',
                      color: '#fff', border: 'none', opacity: generatingCaption ? 0.7 : 1,
                    }}
                  >
                    {generatingCaption ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
                      </svg>
                    )}
                    {generatingCaption ? 'Generating...' : 'AI Generate'}
                  </button>
                </div>
                {(() => {
                  const hasPdfInDrive = driveFiles.some(f => selectedDriveFiles.has(f.id) && (f.name.endsWith('.pdf') || f.mimeType === 'application/pdf'))
                  if (hasPdfInDrive) {
                    return (
                      <input
                        type="text"
                        value={postTitle}
                        onChange={e => setPostTitle(e.target.value)}
                        maxLength={28}
                        placeholder="Carousel title (max 28 chars)..."
                        style={{
                          width: '100%', padding: '10px 12px', fontSize: 13, background: '#1e293b',
                          border: '1px solid rgba(148,163,184,0.2)', borderRadius: 8, color: '#e2e8f0',
                          outline: 'none', marginBottom: 10, fontWeight: 600,
                        }}
                      />
                    )
                  }
                  return null
                })()}
                <textarea
                  value={caption}
                  onChange={e => setCaption(e.target.value)}
                  placeholder="Write your post caption or click AI Generate..."
                  rows={6}
                  style={{
                    width: '100%', padding: '10px 12px', fontSize: 13, background: '#1e293b',
                    border: '1px solid rgba(148,163,184,0.2)', borderRadius: 8, color: '#e2e8f0',
                    outline: 'none', resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.5,
                  }}
                />
                <p style={{ fontSize: 11, color: '#64748b', marginTop: 6 }}>
                  {selectedSlides.size > 0 && slides.find(s => selectedSlides.has(s.id))?.platform === 'youtube'
                    ? 'AI generates SEO-optimized title and description for YouTube Shorts'
                    : 'AI generates SEO-optimized captions with hooks, CTAs, and hashtags based on your market data'}
                </p>
              </div>

              {/* Scheduling */}
              <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid rgba(148,163,184,0.1)', padding: 20 }}>
                <h3 style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 12 }}>Schedule</h3>
                <div className="flex" style={{ gap: 8, marginBottom: 12 }}>
                  <button
                    onClick={() => setSchedulingType('automatic')}
                    style={{
                      flex: 1, padding: '8px', fontSize: 12, borderRadius: 8, cursor: 'pointer', fontWeight: 600,
                      background: schedulingType === 'automatic' ? 'rgba(34,197,94,0.15)' : '#1e293b',
                      color: schedulingType === 'automatic' ? '#22c55e' : '#64748b',
                      border: schedulingType === 'automatic' ? '1px solid rgba(34,197,94,0.3)' : '1px solid rgba(148,163,184,0.1)',
                    }}
                  >
                    Auto Queue
                  </button>
                  <button
                    onClick={() => setSchedulingType('custom')}
                    style={{
                      flex: 1, padding: '8px', fontSize: 12, borderRadius: 8, cursor: 'pointer', fontWeight: 600,
                      background: schedulingType === 'custom' ? 'rgba(99,102,241,0.15)' : '#1e293b',
                      color: schedulingType === 'custom' ? '#818cf8' : '#64748b',
                      border: schedulingType === 'custom' ? '1px solid rgba(99,102,241,0.3)' : '1px solid rgba(148,163,184,0.1)',
                    }}
                  >
                    Custom Time
                  </button>
                </div>
                {schedulingType === 'custom' && (
                  <input
                    type="datetime-local"
                    value={customTime}
                    onChange={e => setCustomTime(e.target.value)}
                    style={{
                      width: '100%', padding: '8px 12px', fontSize: 13, background: '#1e293b',
                      border: '1px solid rgba(148,163,184,0.2)', borderRadius: 8, color: '#e2e8f0', outline: 'none',
                    }}
                  />
                )}
                <label className="flex items-center" style={{ gap: 8, marginTop: 10, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={savingAsDraft}
                    onChange={e => setSavingAsDraft(e.target.checked)}
                    style={{ accentColor: '#6366f1' }}
                  />
                  <span style={{ fontSize: 12, color: '#94a3b8' }}>Save as draft</span>
                </label>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <button
                  onClick={handleUpload}
                  disabled={uploading || selectedCount === 0}
                  className="flex items-center justify-center gap-2 rounded-lg font-semibold"
                  style={{
                    padding: '12px', fontSize: 14, cursor: uploading || selectedCount === 0 ? 'not-allowed' : 'pointer',
                    background: uploading ? '#1e293b' : 'linear-gradient(135deg, #f59e0b, #d97706)',
                    color: '#fff', border: 'none', opacity: selectedCount === 0 ? 0.5 : 1,
                  }}
                >
                  {uploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
                  {uploading ? uploadProgress : `Upload ${selectedCount} slides to Drive`}
                </button>

                <button
                  onClick={handlePost}
                  disabled={posting || uploadCount === 0 || !selectedChannel}
                  className="flex items-center justify-center gap-2 rounded-lg font-semibold"
                  style={{
                    padding: '12px', fontSize: 14, cursor: posting || uploadCount === 0 || !selectedChannel ? 'not-allowed' : 'pointer',
                    background: posting ? '#1e293b' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    color: '#fff', border: 'none', opacity: uploadCount === 0 || !selectedChannel ? 0.5 : 1,
                  }}
                >
                  {posting ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                  {posting ? 'Posting...' : `Post to Buffer (${uploadCount} images)`}
                </button>
              </div>

              {/* Uploaded files */}
              {uploadedFiles.length > 0 && (
                <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid rgba(148,163,184,0.1)', padding: 16 }}>
                  <h3 style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 10 }}>Uploaded Files</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {uploadedFiles.map((f, i) => (
                      <div key={i} className="flex items-center" style={{ gap: 8 }}>
                        {f.link ? (
                          <CheckCircle2 size={14} style={{ color: '#22c55e', flexShrink: 0 }} />
                        ) : (
                          <XCircle size={14} style={{ color: '#ef4444', flexShrink: 0 }} />
                        )}
                        <span style={{ fontSize: 12, color: '#94a3b8', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {f.name}
                        </span>
                        {f.link && (
                          <a href={f.link} target="_blank" rel="noopener noreferrer" style={{ color: '#818cf8' }}>
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Google Drive Files Panel */}
              {driveAuth?.isValid && (
                <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid rgba(148,163,184,0.1)', padding: 16 }}>
                  <div className="flex items-center justify-between" style={{ marginBottom: 8 }}>
                    <div className="flex items-center" style={{ gap: 8 }}>
                      <h3 style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>Google Drive</h3>
                      {(driveFolders.length + driveFiles.length) > 0 && (
                        <label className="flex items-center" style={{ gap: 4, cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={selectedDriveFiles.size === driveFiles.length && driveFiles.length > 0}
                            onChange={selectAllDriveFiles}
                            style={{ accentColor: '#6366f1', width: 12, height: 12 }}
                          />
                          <span style={{ fontSize: 10, color: '#64748b' }}>All</span>
                        </label>
                      )}
                    </div>
                    <div className="flex items-center" style={{ gap: 8 }}>
                      {selectedDriveFiles.size > 0 && (
                        <span style={{ fontSize: 11, color: '#818cf8' }}>{selectedDriveFiles.size} selected</span>
                      )}
                      <button
                        onClick={() => loadDriveFiles(currentFolderId || undefined)}
                        disabled={loadingDriveFiles}
                        style={{ fontSize: 11, color: '#818cf8', background: 'none', border: 'none', cursor: 'pointer' }}
                      >
                        {loadingDriveFiles ? 'Loading...' : 'Refresh'}
                      </button>
                    </div>
                  </div>

                  {/* Breadcrumbs */}
                  {folderPath.length > 0 && (
                    <div className="flex items-center" style={{ gap: 4, marginBottom: 10, flexWrap: 'wrap' }}>
                      <button
                        onClick={() => navigateToBreadcrumb(-1)}
                        style={{ fontSize: 11, color: '#818cf8', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                      >
                        lead-magnet
                      </button>
                      {folderPath.map((f, i) => (
                        <div key={f.id} className="flex items-center" style={{ gap: 4 }}>
                          <span style={{ fontSize: 11, color: '#475569' }}>/</span>
                          <button
                            onClick={() => navigateToBreadcrumb(i)}
                            style={{
                              fontSize: 11, background: 'none', border: 'none', cursor: 'pointer', padding: 0,
                              color: i === folderPath.length - 1 ? '#e2e8f0' : '#818cf8',
                              fontWeight: i === folderPath.length - 1 ? 600 : 400,
                            }}
                          >
                            {f.name}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {loadingDriveFiles ? (
                    <div className="flex items-center justify-center" style={{ padding: 20 }}>
                      <Loader2 size={16} style={{ color: '#818cf8' }} className="animate-spin" />
                    </div>
                  ) : (driveFolders.length + driveFiles.length) === 0 ? (
                    <p style={{ fontSize: 12, color: '#64748b' }}>Empty folder.</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 3, maxHeight: 280, overflowY: 'auto' }}>
                      {/* Folders first */}
                      {driveFolders.map(f => (
                        <div
                          key={f.id}
                          className="flex items-center"
                          style={{
                            gap: 8, padding: '6px 8px', borderRadius: 6, cursor: 'pointer',
                            background: '#1e293b', border: '1px solid transparent',
                          }}
                          onClick={() => navigateToFolder(f.id, f.name)}
                        >
                          <FolderIcon size={14} style={{ color: '#f59e0b', flexShrink: 0 }} />
                          <span style={{ fontSize: 12, color: '#e2e8f0', flex: 1, fontWeight: 500 }}>
                            {f.name}
                          </span>
                        </div>
                      ))}

                      {/* Files */}
                      {driveFiles.map(f => {
                        const isSelected = selectedDriveFiles.has(f.id)
                        return (
                          <div
                            key={f.id}
                            className="flex items-center"
                            style={{
                              gap: 8, padding: '6px 8px', borderRadius: 6, cursor: 'pointer',
                              background: isSelected ? 'rgba(99,102,241,0.1)' : 'transparent',
                              border: isSelected ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent',
                            }}
                            onClick={() => toggleDriveFile(f.id)}
                          >
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleDriveFile(f.id)}
                              onClick={e => e.stopPropagation()}
                              style={{ accentColor: '#6366f1', width: 12, height: 12, flexShrink: 0 }}
                            />
                            {f.name.endsWith('.pdf') ? (
                              <FileText size={14} style={{ color: '#f59e0b', flexShrink: 0 }} />
                            ) : (
                              <ImageIcon size={14} style={{ color: '#818cf8', flexShrink: 0 }} />
                            )}
                            <span style={{ fontSize: 12, color: '#94a3b8', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {f.name}
                            </span>
                            <button
                              onClick={(e) => { e.stopPropagation(); deleteDriveFile(f.id, f.name) }}
                              disabled={deletingFile === f.id}
                              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, display: 'flex', flexShrink: 0 }}
                            >
                              {deletingFile === f.id ? (
                                <Loader2 size={12} style={{ color: '#f59e0b' }} className="animate-spin" />
                              ) : (
                                <Trash2 size={12} style={{ color: '#ef4444' }} />
                              )}
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Schedule & Delete selected Drive files */}
                  {selectedDriveFiles.size > 0 && (
                    <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(148,163,184,0.1)' }}>
                      <div className="flex" style={{ gap: 8 }}>
                        <button
                          onClick={handleScheduleDriveFiles}
                          disabled={!selectedChannel}
                          className="flex items-center justify-center gap-2 rounded-lg font-semibold"
                          style={{
                            flex: 1, padding: '10px', fontSize: 12, cursor: !selectedChannel ? 'not-allowed' : 'pointer',
                            background: !selectedChannel ? '#1e293b' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            color: '#fff', border: 'none', opacity: !selectedChannel ? 0.5 : 1,
                          }}
                        >
                          <Send size={14} />
                          Schedule {selectedDriveFiles.size}
                        </button>
                        <button
                          onClick={deleteSelectedDriveFiles}
                          className="flex items-center justify-center gap-2 rounded-lg font-semibold"
                          style={{
                            padding: '10px 14px', fontSize: 12, cursor: 'pointer',
                            background: 'linear-gradient(135deg, #ef4444, #dc2626)',
                            color: '#fff', border: 'none',
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Post result */}
              {postResult && (
                <div style={{
                  background: postResult.data?.createPost?.post ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                  borderRadius: 12, border: `1px solid ${postResult.data?.createPost?.post ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
                  padding: 16,
                }}>
                  {postResult.data?.createPost?.post ? (
                    <div>
                      <div className="flex items-center" style={{ gap: 8, marginBottom: 6 }}>
                        <CheckCircle2 size={16} style={{ color: '#22c55e' }} />
                        <span style={{ fontSize: 13, fontWeight: 600, color: '#22c55e' }}>Post created!</span>
                      </div>
                      <p style={{ fontSize: 12, color: '#94a3b8' }}>Status: {postResult.data.createPost.post.status}</p>
                      <p style={{ fontSize: 12, color: '#94a3b8' }}>ID: {postResult.data.createPost.post.id}</p>
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center" style={{ gap: 8, marginBottom: 6 }}>
                        <XCircle size={16} style={{ color: '#ef4444' }} />
                        <span style={{ fontSize: 13, fontWeight: 600, color: '#ef4444' }}>Error</span>
                      </div>
                      <p style={{ fontSize: 12, color: '#fca5a5' }}>
                        {postResult.data?.createPost?.message || postResult.error || 'Unknown error'}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
