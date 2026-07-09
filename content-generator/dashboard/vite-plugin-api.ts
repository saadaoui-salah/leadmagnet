import type { Plugin } from 'vite'
import { exec } from 'node:child_process'
import { promisify } from 'node:util'
import path from 'node:path'
import fs from 'node:fs'

const execAsync = promisify(exec)

const ROOT = path.resolve(__dirname, '..')
const CONFIG_PATH = path.join(__dirname, '.env.json')

interface GenerationStatus {
  running: boolean
  step: string
  progress: number
  error: string | null
  lastRun: string | null
}

interface Config {
  bufferApiKey?: string
  googleDriveCredentials?: string
  googleDriveFolderId?: string
  bufferOrgId?: string
  bufferChannels?: { id: string; name: string; service: string }[]
}

const status: GenerationStatus = {
  running: false,
  step: '',
  progress: 0,
  error: null,
  lastRun: null,
}

function loadConfig(): Config {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'))
    }
  } catch {}
  return {}
}

function saveConfig(config: Config) {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2))
}

function getRequestBody(req: any): Promise<any> {
  return new Promise((resolve, reject) => {
    let body = ''
    req.on('data', (chunk: string) => body += chunk)
    req.on('end', () => {
      try { resolve(JSON.parse(body)) }
      catch { resolve({}) }
    })
    req.on('error', reject)
  })
}

async function runPipeline() {
  if (status.running) return
  status.running = true
  status.error = null
  status.progress = 0

  try {
    status.step = 'Fetching market data & generating copy...'
    status.progress = 8
    const pythonCmd = process.platform === 'win32'
      ? 'python scripts/generate_market_copy.py'
      : 'python3 scripts/generate_market_copy.py'
    await execAsync(pythonCmd, { cwd: ROOT, maxBuffer: 10 * 1024 * 1024 })

    status.step = 'Exporting LinkedIn slides as PDF...'
    status.progress = 28
    const linkedinCmd = process.platform === 'win32'
      ? 'powershell -ExecutionPolicy Bypass -File scripts/export-linkedin-pdf.ps1'
      : 'node scripts/export-images.mjs'
    await execAsync(linkedinCmd, { cwd: ROOT, maxBuffer: 10 * 1024 * 1024 })

    status.step = 'Exporting Instagram slides...'
    status.progress = 48
    const igCmd = process.platform === 'win32'
      ? 'powershell -ExecutionPolicy Bypass -File scripts/export-instagram-images.ps1'
      : 'node scripts/export-instagram-images.mjs'
    await execAsync(igCmd, { cwd: ROOT, maxBuffer: 10 * 1024 * 1024 })

    status.step = 'Generating Shorts TTS audio...'
    status.progress = 60
    const audioCmd = process.platform === 'win32'
      ? 'powershell -ExecutionPolicy Bypass -File scripts/generate-shorts-audio.ps1'
      : 'node scripts/generate-shorts-audio.mjs'
    await execAsync(audioCmd, { cwd: ROOT, maxBuffer: 10 * 1024 * 1024 })

    status.step = 'Rendering YouTube Shorts video...'
    status.progress = 72
    const shortsCmd = process.platform === 'win32'
      ? 'powershell -ExecutionPolicy Bypass -File scripts/export-youtube-shorts.ps1'
      : 'node scripts/export-youtube-shorts.mjs'
    await execAsync(shortsCmd, { cwd: ROOT, maxBuffer: 50 * 1024 * 1024 })

    status.step = 'Syncing output to dashboard...'
    status.progress = 94
    const syncCmd = process.platform === 'win32'
      ? 'xcopy /E /I /Y out\\linkedin dashboard\\public\\out\\linkedin & xcopy /E /I /Y out\\instagram dashboard\\public\\out\\instagram & xcopy /E /I /Y out\\youtube-shorts dashboard\\public\\out\\youtube-shorts'
      : 'cp -r out/linkedin dashboard/public/out/linkedin && cp -r out/instagram dashboard/public/out/instagram && cp -r out/youtube-shorts dashboard/public/out/youtube-shorts'
    await execAsync(syncCmd, { cwd: ROOT, maxBuffer: 10 * 1024 * 1024 })

    status.step = 'Done!'
    status.progress = 100
    status.lastRun = new Date().toISOString()
  } catch (err: any) {
    status.error = err.message || 'Generation failed'
    status.step = 'Error'
  } finally {
    status.running = false
  }
}

// Google Drive: get access token from cached token or refresh
async function getDriveAccessToken(_credentialsJson: string): Promise<string> {
  // Check for cached token first
  const tokenPath = path.join(__dirname, '.drive-token.json')
  if (fs.existsSync(tokenPath)) {
    const cached = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'))
    if (cached.expiry_date && cached.expiry_date > Date.now() + 60000) {
      return cached.access_token
    }
    // Try refresh if we have a refresh token
    if (cached.refresh_token) {
      const refreshed = await refreshDriveToken(cached.refresh_token)
      return refreshed
    }
  }

  throw new Error('No valid Google Drive token. Please authorize via Settings → Authorize Google Drive.')
}

async function refreshDriveToken(refreshToken: string): Promise<string> {
  const config = loadConfig()
  const creds = config.googleDriveCredentials ? JSON.parse(config.googleDriveCredentials) : null
  const driveCreds = creds?.installed || creds
  if (!driveCreds?.client_id || !driveCreds?.client_secret) throw new Error('Missing client credentials for refresh')

  const resp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
      client_id: driveCreds.client_id,
      client_secret: driveCreds.client_secret,
    }),
  })

  const data: any = await resp.json()
  if (!data.access_token) throw new Error('Failed to refresh token')

  // Save updated token
  const tokenPath = path.join(__dirname, '.drive-token.json')
  const existing = fs.existsSync(tokenPath) ? JSON.parse(fs.readFileSync(tokenPath, 'utf-8')) : {}
  fs.writeFileSync(tokenPath, JSON.stringify({
    ...existing,
    access_token: data.access_token,
    expiry_date: Date.now() + (data.expires_in || 3600) * 1000,
  }))

  return data.access_token
}

// Upload file to Google Drive and return shareable link
async function uploadToDrive(
  accessToken: string,
  filePath: string,
  fileName: string,
  mimeType: string,
  folderId?: string,
): Promise<{ id: string; link: string }> {
  const fileBytes = fs.readFileSync(filePath)

  // Upload to Drive
  const metadata: any = { name: fileName, mimeType }
  if (folderId) metadata.parents = [folderId]

  const form = new FormData()
  form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }))
  form.append('file', new Blob([fileBytes], { type: mimeType }))

  const uploadResp = await fetch(
    'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}` },
      body: form,
    },
  )
  const uploadData: any = await uploadResp.json()
  if (!uploadData.id) throw new Error(`Upload failed: ${JSON.stringify(uploadData)}`)

  // Make publicly accessible
  await fetch(
    `https://www.googleapis.com/drive/v3/files/${uploadData.id}/permissions`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ role: 'reader', type: 'anyone' }),
    },
  )

  // Return direct link
  const link = `https://drive.google.com/uc?export=view&id=${uploadData.id}`
  return { id: uploadData.id, link }
}

// Buffer API proxy
async function bufferGraphQL(apiKey: string, query: string, variables?: any) {
  const resp = await fetch('https://api.buffer.com', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ query, variables }),
  })

  if (resp.status === 429) {
    return { errors: [{ message: 'Rate limited by Buffer API. Please try again later.', extensions: { code: 'RATE_LIMIT_EXCEEDED' } }] }
  }

  if (!resp.ok) {
    return { errors: [{ message: `Buffer API error: ${resp.status} ${resp.statusText}` }] }
  }

  return resp.json()
}

export function apiPlugin(): Plugin {
  return {
    name: 'vite-plugin-api',
    configureServer(server) {
      // Config endpoints
      server.middlewares.use('/api/config', async (req, res) => {
        res.setHeader('Content-Type', 'application/json')
        if (req.method === 'GET') {
          const config = loadConfig()
          res.end(JSON.stringify({
            bufferApiKey: config.bufferApiKey ? '***' + config.bufferApiKey.slice(-4) : null,
            hasGoogleDrive: !!config.googleDriveCredentials,
            googleDriveFolderId: config.googleDriveFolderId || null,
          }))
        } else if (req.method === 'POST') {
          const body = await getRequestBody(req)
          const config = loadConfig()
          if (body.bufferApiKey !== undefined) config.bufferApiKey = body.bufferApiKey
          if (body.googleDriveCredentials !== undefined) config.googleDriveCredentials = body.googleDriveCredentials
          if (body.googleDriveFolderId !== undefined) config.googleDriveFolderId = body.googleDriveFolderId
          saveConfig(config)
          res.end(JSON.stringify({ ok: true }))
        }
      })

      // Generation endpoints
      server.middlewares.use('/api/generate', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }
        if (status.running) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Generation already in progress' }))
          return
        }
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ ok: true, message: 'Generation started' }))
        runPipeline()
      })

      server.middlewares.use('/api/status', async (_req, res) => {
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify(status))
      })

      // Google Drive OAuth2: get auth URL
      server.middlewares.use('/api/drive/auth-url', async (_req, res) => {
        res.setHeader('Content-Type', 'application/json')

        try {
          const config = loadConfig()
          if (!config.googleDriveCredentials) {
            res.end(JSON.stringify({ error: 'Google Drive credentials not configured' }))
            return
          }

          const creds = JSON.parse(config.googleDriveCredentials)
          // Support both formats: {installed: {client_id...}} or {client_id...}
          const driveCreds = creds.installed || creds
          if (!driveCreds.client_id) {
            res.end(JSON.stringify({ error: 'client_id not found in credentials' }))
            return
          }

          const redirectUri = 'http://localhost:3000/api/drive/callback'
          const scopes = ['https://www.googleapis.com/auth/drive.file']
          const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${driveCreds.client_id}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${encodeURIComponent(scopes.join(' '))}&access_type=offline&prompt=consent`

          res.end(JSON.stringify({ ok: true, url: authUrl }))
        } catch (err: any) {
          res.end(JSON.stringify({ error: err.message }))
        }
      })

      // Google Drive OAuth2: handle callback
      server.middlewares.use('/api/drive/callback', async (req, res) => {
        const url = new URL(req.url!, `http://${req.headers.host}`)
        const code = url.searchParams.get('code')
        const error = url.searchParams.get('error')

        const errorPage = (msg: string) => `<!DOCTYPE html><html><body><script>
          window.opener.postMessage({ type: 'drive-auth', success: false, error: '${msg}' }, '*');
          document.body.innerHTML = '<h2 style="font-family:sans-serif;text-align:center;margin-top:40px;color:#ef4444">Drive Auth Failed</h2><p style="font-family:sans-serif;text-align:center;color:#94a3b8">${msg}</p>';
          setTimeout(() => window.close(), 2000);
        </script></body></html>`

        if (error) {
          res.setHeader('Content-Type', 'text/html')
          res.end(errorPage(error))
          return
        }

        if (!code) {
          res.setHeader('Content-Type', 'text/html')
          res.end(errorPage('No authorization code received'))
          return
        }

        try {
          const config = loadConfig()
          const creds = config.googleDriveCredentials ? JSON.parse(config.googleDriveCredentials) : null
          const driveCreds = creds?.installed || creds
          if (!driveCreds?.client_id || !driveCreds?.client_secret) {
            res.setHeader('Content-Type', 'text/html')
            res.end(errorPage('No credentials configured'))
            return
          }

          const redirectUri = 'http://localhost:3000/api/drive/callback'

          // Exchange code for tokens
          const tokenResp = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
              code,
              client_id: driveCreds.client_id,
              client_secret: driveCreds.client_secret,
              redirect_uri: redirectUri,
              grant_type: 'authorization_code',
            }),
          })

          const tokenData: any = await tokenResp.json()
          if (!tokenData.access_token) {
            res.writeHead(302, { Location: `http://localhost:3000?drive_error=${tokenData.error || 'token_exchange_failed'}` })
            res.end()
            return
          }

          // Save token
          const tokenPath = path.join(__dirname, '.drive-token.json')
          fs.writeFileSync(tokenPath, JSON.stringify({
            access_token: tokenData.access_token,
            refresh_token: tokenData.refresh_token,
            expiry_date: Date.now() + (tokenData.expires_in || 3600) * 1000,
            token_type: tokenData.token_type,
          }))

          // Return HTML that notifies parent window and closes tab
          res.setHeader('Content-Type', 'text/html')
          res.end(`<!DOCTYPE html><html><body><script>
            window.opener.postMessage({ type: 'drive-auth', success: true }, '*');
            document.body.innerHTML = '<h2 style="font-family:sans-serif;text-align:center;margin-top:40px;color:#22c55e">Google Drive Connected!</h2><p style="font-family:sans-serif;text-align:center;color:#94a3b8">You can close this tab.</p>';
            setTimeout(() => window.close(), 1500);
          </script></body></html>`)
        } catch (err: any) {
          res.setHeader('Content-Type', 'text/html')
          res.end(errorPage(err.message))
        }
      })

      // Google Drive: check auth status
      server.middlewares.use('/api/drive/status', async (_req, res) => {
        res.setHeader('Content-Type', 'application/json')

        const tokenPath = path.join(__dirname, '.drive-token.json')
        const hasToken = fs.existsSync(tokenPath)
        let isValid = false
        let expiresAt = null

        if (hasToken) {
          const token = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'))
          expiresAt = token.expiry_date
          isValid = token.expiry_date > Date.now()
        }

        res.end(JSON.stringify({ ok: true, hasToken, isValid, expiresAt }))
      })

      // Google Drive: disconnect
      server.middlewares.use('/api/drive/disconnect', async (_req, res) => {
        res.setHeader('Content-Type', 'application/json')

        const tokenPath = path.join(__dirname, '.drive-token.json')
        if (fs.existsSync(tokenPath)) {
          fs.unlinkSync(tokenPath)
        }

        res.end(JSON.stringify({ ok: true }))
      })

      // Google Drive upload endpoint
      server.middlewares.use('/api/drive/upload', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }

        res.setHeader('Content-Type', 'application/json')

        try {
          const config = loadConfig()
          if (!config.googleDriveCredentials) {
            res.end(JSON.stringify({ error: 'Google Drive credentials not configured' }))
            return
          }

          const body = await getRequestBody(req)
          const { files, platform } = body as { files: { path: string; name: string; mimeType: string }[]; platform?: string }

          const accessToken = await getDriveAccessToken(config.googleDriveCredentials)

          // Find or create "lead-magnet" folder
          let folderId = config.googleDriveFolderId
          if (!folderId) {
            // Search for existing folder
            const searchResp = await fetch(
              `https://www.googleapis.com/drive/v3/files?q=name='lead-magnet' and mimeType='application/vnd.google-apps.folder' and trashed=false`,
              { headers: { Authorization: `Bearer ${accessToken}` } }
            )
            const searchData: any = await searchResp.json()
            if (searchData.files && searchData.files.length > 0) {
              folderId = searchData.files[0].id
            } else {
              // Create the folder
              const createResp = await fetch(
                'https://www.googleapis.com/drive/v3/files',
                {
                  method: 'POST',
                  headers: {
                    Authorization: `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    name: 'lead-magnet',
                    mimeType: 'application/vnd.google-apps.folder',
                  }),
                }
              )
              const createData: any = await createResp.json()
              folderId = createData.id
              // Save folder ID to config
              config.googleDriveFolderId = folderId
              saveConfig(config)
            }
          }

          // Find or create platform subfolder
          let targetFolderId = folderId
          if (platform) {
            const folderName = platform.charAt(0).toUpperCase() + platform.slice(1)
            const subSearchResp = await fetch(
              `https://www.googleapis.com/drive/v3/files?q=name='${folderName}' and '${folderId}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false`,
              { headers: { Authorization: `Bearer ${accessToken}` } }
            )
            const subSearchData: any = await subSearchResp.json()
            if (subSearchData.files && subSearchData.files.length > 0) {
              targetFolderId = subSearchData.files[0].id
            } else {
              const subCreateResp = await fetch(
                'https://www.googleapis.com/drive/v3/files',
                {
                  method: 'POST',
                  headers: {
                    Authorization: `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    name: folderName,
                    mimeType: 'application/vnd.google-apps.folder',
                    parents: [folderId],
                  }),
                }
              )
              const subCreateData: any = await subCreateResp.json()
              targetFolderId = subCreateData.id
            }
          }

          const results = []
          for (const file of files) {
            const fullPath = path.join(ROOT, file.path)
            if (!fs.existsSync(fullPath)) {
              results.push({ name: file.name, error: 'File not found' })
              continue
            }
            const result = await uploadToDrive(
              accessToken, fullPath, file.name, file.mimeType, targetFolderId,
            )
            results.push({ name: file.name, ...result })
          }

          res.end(JSON.stringify({ ok: true, files: results, folderId: targetFolderId }))
        } catch (err: any) {
          res.end(JSON.stringify({ error: err.message }))
        }
      })

      // Google Drive: list files in folder
      server.middlewares.use('/api/drive/files', async (req, res) => {
        res.setHeader('Content-Type', 'application/json')

        try {
          const config = loadConfig()
          if (!config.googleDriveCredentials) {
            res.end(JSON.stringify({ error: 'No Google Drive credentials' }))
            return
          }
          const accessToken = await getDriveAccessToken(config.googleDriveCredentials)
          if (!accessToken) {
            res.end(JSON.stringify({ error: 'Not authenticated with Google Drive' }))
            return
          }

          // Parse folderId from query string
          const url = new URL(req.url || '/', `http://${req.headers.host}`)
          const targetFolderId = url.searchParams.get('folderId') || config.googleDriveFolderId

          if (!targetFolderId) {
            res.end(JSON.stringify({ ok: true, folders: [], files: [], folderId: null, parentFolderId: null }))
            return
          }

          // List contents in the folder
          const query = encodeURIComponent(`'${targetFolderId}' in parents and trashed=false`)
          const response = await fetch(
            `https://www.googleapis.com/drive/v3/files?q=${query}&fields=files(id,name,mimeType,size,createdTime,modifiedTime)&orderBy=name`,
            { headers: { Authorization: `Bearer ${accessToken}` } }
          )
          const data: any = await response.json()

          if (!response.ok) {
            res.end(JSON.stringify({ error: data.error?.message || 'Failed to list files' }))
            return
          }

          const allItems = data.files || []
          const folders = allItems.filter((f: any) => f.mimeType === 'application/vnd.google-apps.folder')
          const files = allItems.filter((f: any) => f.mimeType !== 'application/vnd.google-apps.folder')

          // Get parent folder ID for breadcrumb navigation
          let parentFolderId = null
          if (targetFolderId !== config.googleDriveFolderId) {
            // Fetch current folder metadata to get parent
            const metaResp = await fetch(
              `https://www.googleapis.com/drive/v3/files/${targetFolderId}?fields=parents`,
              { headers: { Authorization: `Bearer ${accessToken}` } }
            )
            const meta: any = await metaResp.json()
            parentFolderId = meta.parents?.[0] || config.googleDriveFolderId
          }

          res.end(JSON.stringify({
            ok: true,
            folders,
            files,
            folderId: targetFolderId,
            parentFolderId,
            rootFolderId: config.googleDriveFolderId,
          }))
        } catch (err: any) {
          res.end(JSON.stringify({ error: err.message }))
        }
      })

      // Google Drive: delete file
      server.middlewares.use('/api/drive/delete', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }

        res.setHeader('Content-Type', 'application/json')

        try {
          const config = loadConfig()
          if (!config.googleDriveCredentials) {
            res.end(JSON.stringify({ error: 'No Google Drive credentials' }))
            return
          }
          const accessToken = await getDriveAccessToken(config.googleDriveCredentials)
          if (!accessToken) {
            res.end(JSON.stringify({ error: 'Not authenticated with Google Drive' }))
            return
          }

          const chunks: Buffer[] = []
          for await (const chunk of req) chunks.push(chunk)
          const body = JSON.parse(Buffer.concat(chunks).toString())
          const { fileId } = body

          if (!fileId) {
            res.end(JSON.stringify({ error: 'fileId required' }))
            return
          }

          const response = await fetch(
            `https://www.googleapis.com/drive/v3/files/${fileId}`,
            { method: 'DELETE', headers: { Authorization: `Bearer ${accessToken}` } }
          )

          if (!response.ok) {
            const data: any = await response.json()
            res.end(JSON.stringify({ error: data.error?.message || 'Failed to delete file' }))
            return
          }

          res.end(JSON.stringify({ ok: true, deleted: fileId }))
        } catch (err: any) {
          res.end(JSON.stringify({ error: err.message }))
        }
      })

      // Buffer channels endpoint — returns cached channels from config
      server.middlewares.use('/api/buffer/channels', async (_req, res) => {
        res.setHeader('Content-Type', 'application/json')

        try {
          const config = loadConfig()
          if (!config.bufferApiKey) {
            res.end(JSON.stringify({ error: 'Buffer API key not configured' }))
            return
          }

          // Return cached channels if available
          if (config.bufferChannels && config.bufferChannels.length > 0) {
            res.end(JSON.stringify({ ok: true, channels: config.bufferChannels, cached: true }))
            return
          }

          // No cached channels — tell client to refresh
          res.end(JSON.stringify({ ok: true, channels: [], cached: true, needsRefresh: true }))
        } catch (err: any) {
          res.end(JSON.stringify({ error: err.message }))
        }
      })

      // Buffer channels refresh — fetches from API and saves to config
      server.middlewares.use('/api/buffer/channels/refresh', async (_req, res) => {
        res.setHeader('Content-Type', 'application/json')

        try {
          const config = loadConfig()
          if (!config.bufferApiKey) {
            res.end(JSON.stringify({ error: 'Buffer API key not configured' }))
            return
          }

          // Step 1: Get organization ID
          const orgData: any = await bufferGraphQL(config.bufferApiKey, `
            query GetOrganizations {
              account {
                organizations {
                  id
                  name
                }
              }
            }
          `)

          if (orgData.errors) {
            res.end(JSON.stringify({ error: orgData.errors[0]?.message || 'GraphQL error' }))
            return
          }

          const orgs = orgData?.data?.account?.organizations || []
          if (orgs.length === 0) {
            res.end(JSON.stringify({ ok: true, channels: [] }))
            return
          }

          const orgId = orgs[0].id

          // Step 2: Get channels for this organization
          const channelData: any = await bufferGraphQL(config.bufferApiKey, `
            query GetChannels {
              channels(input: { organizationId: "${orgId}" }) {
                id
                name
                service
              }
            }
          `)

          if (channelData.errors) {
            res.end(JSON.stringify({ error: channelData.errors[0]?.message || 'GraphQL error' }))
            return
          }

          const channels = channelData?.data?.channels || []

          // Save to config
          config.bufferOrgId = orgId
          config.bufferChannels = channels
          saveConfig(config)

          res.end(JSON.stringify({ ok: true, channels }))
        } catch (err: any) {
          res.end(JSON.stringify({ error: err.message }))
        }
      })

      // Buffer create post endpoint
      server.middlewares.use('/api/buffer/post', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }

        res.setHeader('Content-Type', 'application/json')

        try {
          const config = loadConfig()
          if (!config.bufferApiKey) {
            res.end(JSON.stringify({ error: 'Buffer API key not configured' }))
            return
          }

          const body = await getRequestBody(req)
          const { channelId, text, assets: rawAssets, schedulingType, mode, dueAt } = body

          // Build assets - support both image URLs and document objects
          const assets = (rawAssets || []).map((a: any) => {
            if (a.type === 'document') {
              return {
                document: {
                  url: a.url,
                  title: a.title || 'LinkedIn Carousel',
                  thumbnailUrl: a.thumbnailUrl || a.url,
                },
              }
            }
            return { image: { url: a.url || a } }
          })

          const input: any = {
            channelId,
            text,
            schedulingType: schedulingType || 'automatic',
            mode: mode || 'addToQueue',
            assets,
          }

          if (dueAt) input.dueAt = dueAt

          const data = await bufferGraphQL(config.bufferApiKey, `
            mutation CreatePost($input: CreatePostInput!) {
              createPost(input: $input) {
                ... on PostActionSuccess {
                  post {
                    id
                    text
                    status
                    assets {
                      id
                      mimeType
                    }
                  }
                }
                ... on MutationError {
                  message
                }
              }
            }
          `, { input }) as any

          // Check for rate limit or other errors
          if (data.errors) {
            res.end(JSON.stringify({ error: data.errors[0]?.message || 'Unknown error', details: data }))
            return
          }

          res.end(JSON.stringify(data))
        } catch (err: any) {
          res.end(JSON.stringify({ error: err.message }))
        }
      })

      // Caption generation endpoint
      server.middlewares.use('/api/generate-caption', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }

        res.setHeader('Content-Type', 'application/json')

        try {
          const body = await getRequestBody(req)
          const { platform, marketData, slideCount: _slideCount } = body

          // Load generated market data if not provided
          let data = marketData
          if (!data) {
            const marketPath = path.join(ROOT, 'src', 'data', 'generatedMarket.json')
            if (fs.existsSync(marketPath)) {
              data = JSON.parse(fs.readFileSync(marketPath, 'utf-8'))
            }
          }

          const copy = data?.generatedCopy || {}
          const topZips = (data?.topZipCodes || []).slice(0, 5)

          const zipList = topZips.map((z: any) =>
            `  - ${z.zipCode || z.zip}: $${z.medianRent || z.avgRent || 'N/A'}/mo, +${z.rentGrowth30d || z.rentGrowth || 'N/A'}% growth, ${z.activeListings || 'N/A'} listings`
          ).join('\n')

          const marketSection = `MARKET DATA:
- City: ${data?.city || 'New York'}, ${data?.state || 'NY'}
- ZIP: ${data?.zipCode || data?.zipcode || '10001'}
- Active Listings: ${data?.activeListings || 'N/A'}
- Median Rent: $${data?.medianRent || data?.avg_rent || 'N/A'}
- Monthly Growth: ${data?.monthlyGrowth || copy.monthlyGrowth || 'N/A'}%
- Yearly Growth: ${data?.yearlyGrowth || copy.yearlyGrowth || 'N/A'}%
- Avg Days on Market: ${data?.avgDaysOnMarket || 'N/A'}

TOP GROWING ZIP CODES:
${zipList}

HOOK:
${copy.hook || 'N/A'}

CTA:
${copy.ctaHeadline || 'N/A'}`

          const prompts: Record<string, string> = {
            linkedin: `Output EXACTLY in this format — title on the first line, then a blank line, then the caption:

[Short compelling title, MAX 28 characters, no quotes, no labels]

[LinkedIn caption]

RULES:
- Title MUST be 28 characters or fewer (strict limit)
- Title must be a punchy headline (not "Title:" label)
- Caption starts immediately after the blank line
- Do NOT include "Caption:", "Title:", "Here's", explanations, labels, quotation marks, or markdown

You are a top-performing LinkedIn content strategist specializing in real estate intelligence, market analytics, and B2B audience growth.

Your writing should feel like a human analyst sharing a valuable market observation, not an AI, marketer, or salesperson.

${marketSection}

OBJECTIVE:
Create a LinkedIn post that:
- Feels written by a real market analyst
- Sparks curiosity
- Provides useful insight
- Encourages discussion
- Builds authority
- Attracts investors, brokers, agents, property managers, and real estate professionals

STRUCTURE:
1. Pattern-interrupt hook (1 line)
2. Observation from the data
3. Why this matters
4. One unexpected insight or implication
5. Question to encourage comments
6. Soft CTA
7. 3-5 highly relevant hashtags

WRITING STYLE:
- Human
- Insightful
- Concise
- Data-driven
- Conversational
- Professional
- Confident

Avoid:
- Generic motivational language
- Corporate jargon
- Excessive emojis
- Clickbait
- Obvious AI phrasing
- "In today's market"
- "Game changer"
- "Unlock"
- "Revolutionize"
- "Dive into"
- "Imagine"

Use:
- Specific numbers
- Contrarian observations when supported by data
- Short paragraphs
- Natural sentence variation
- Thought-provoking questions

The post should read like something a real estate analyst with 10+ years of experience would publish after reviewing the data.

Length: 120-220 words.

Use the provided data naturally throughout the post.

End with 3-5 relevant LinkedIn hashtags.`,

            instagram: `Output ONLY the final Instagram caption.

Do NOT include:
- "Caption:"
- "Instagram Post:"
- Explanations
- Labels
- Quotation marks
- Markdown formatting

Start immediately with the hook.

You are an elite Instagram growth strategist, real estate content creator, and viral storytelling expert.

Your job is to transform Zillow market data into highly engaging Instagram captions that maximize:
- Saves
- Shares
- Comments
- Follows
- Profile visits

${marketSection}

OBJECTIVE:
Create a caption that makes people:
- Stop scrolling
- Read the entire caption
- Swipe through the carousel
- Save the post
- Share it with someone interested in real estate

STRUCTURE:
1. Attention-grabbing hook
2. Why the data is surprising
3. What happened
4. What it means in plain English
5. One curiosity-inducing takeaway
6. Save/share CTA
7. Follow CTA
8. 15-20 highly relevant hashtags

WRITING STYLE:
- Human
- Conversational
- Curious
- Insightful
- Easy to read
- Short paragraphs
- Mobile optimized

Use:
- Line breaks
- Occasional emojis (max 3-5)
- Specific numbers
- Real data points
- Natural language

Avoid:
- Corporate language
- Generic AI phrases
- Long paragraphs
- Buzzwords
- "Unlock"
- "Game changer"
- "Revolutionary"
- "In today's market"
- "Dive into"

PSYCHOLOGY:
Write like a knowledgeable friend who just discovered something interesting in the housing market and can't wait to share it.

Create curiosity without clickbait.

Make readers think:
"Wow, I didn't know that."
"I should save this."
"I need to see the next slide."

Length: 150-300 words.

Finish with:
- Save CTA
- Follow CTA
- 15-20 niche real estate hashtags

Output ONLY the final caption.`,

            facebook: `Output ONLY the final Facebook post.

Do NOT include:
- "Facebook Post:"
- "Caption:"
- Explanations
- Labels
- Quotation marks
- Markdown headings

Start immediately with the opening line.

You are a top Facebook content creator specializing in real estate trends, housing markets, local communities, and data storytelling.

Your job is to transform Zillow market data into highly engaging Facebook posts that encourage:
- Comments
- Shares
- Saves
- Discussions
- Follows

${marketSection}

OBJECTIVE:
Create a Facebook post that feels like a local market update people would want to discuss with friends, neighbors, investors, or family members.

FACEBOOK PSYCHOLOGY:
People engage with:
- Local trends
- Surprising facts
- Community impact
- Housing affordability
- Personal experiences
- Future predictions

The post should make readers think:
- "I didn't know that."
- "That's happening in my area too."
- "What do you think?"
- "I should share this."

STRUCTURE:
1. Strong attention-grabbing opening
2. Explain the key market movement using real numbers
3. Translate the data into real-world impact
4. Highlight one surprising insight
5. Ask an engaging question
6. Soft follow/share CTA
7. 3-8 relevant hashtags

WRITING STYLE:
- Human
- Friendly
- Conversational
- Community-focused
- Easy to understand

Use:
- Short paragraphs
- Real numbers
- Plain English
- Occasional emoji (0-3 max)
- Natural storytelling

Avoid:
- Corporate language
- Sales language
- AI-sounding phrases
- Excessive hype
- Buzzwords
- Long walls of text

SPECIAL RULE:
Do not just report the numbers.

Explain what those numbers mean for:
- Renters
- Homebuyers
- Investors
- Local residents

Length: 120-250 words.

End with a question that encourages comments and discussion.

Output ONLY the final Facebook post.`,

            threads: `Output ONLY the final Threads post.

Do NOT include:
- "Threads Post:"
- "Caption:"
- Explanations
- Labels
- Quotation marks
- Markdown headings

Start immediately with the opening line.

You are a top Threads creator specializing in real estate, economics, housing trends, and market observations.

Your job is to turn Zillow market data into highly engaging Threads posts that feel human, conversational, and discussion-worthy.

${marketSection}

OBJECTIVE:
Create a Threads post that:
- Feels like a spontaneous observation
- Sparks replies and debate
- Encourages reposts
- Builds authority naturally
- Sounds written by a real person

THREADS PSYCHOLOGY:
People on Threads engage with:
- Hot takes
- Contrarian observations
- Surprising statistics
- Questions
- Personal opinions
- Quick insights

Avoid sounding like:
- A company
- A newsletter
- A report
- LinkedIn

Instead sound like:
- A smart market observer
- Someone sharing a fascinating discovery
- A person thinking out loud

STRUCTURE:
1. Strong observation or surprising statement
2. One or two supporting data points
3. Why this caught your attention
4. What it could mean
5. End with an open-ended question

WRITING STYLE:
- Human
- Conversational
- Curious
- Opinionated when supported by data
- Short sentences
- Natural rhythm

Use:
- Real numbers
- Occasional emojis (0-2 max)
- Plain language
- Thought-provoking questions

Avoid:
- Corporate language
- Sales language
- CTA-heavy posts
- Generic AI phrasing
- Excessive hashtags

GOOD EXAMPLES:
"One ZIP code in New York just saw rents jump 14.2% in a month.

That's not normal.

What's interesting is inventory didn't increase enough to explain the demand surge.

Makes me wonder whether we're seeing the beginning of a broader neighborhood shift.

Would you pay more to live there if the trend continues?"

Length: 80-180 words.

End with a genuine question that invites discussion.

Use at most 1-3 relevant hashtags if they feel natural.

Output ONLY the final post.`,

            youtube: `Output ONLY the final YouTube content.

Do NOT include:
- "Title:"
- "Description:"
- Explanations
- Labels
- Markdown formatting
- Quotation marks

Return EXACTLY:

First line:
The YouTube title

Blank line

Then:
The YouTube description

MARKET DATA:
- City: ${data?.city || 'New York'}, ${data?.state || 'NY'}
- ZIP: ${data?.zipCode || data?.zipcode || '10001'}
- Active Listings: ${data?.activeListings || 'N/A'}
- Median Rent: $${data?.medianRent || data?.avg_rent || 'N/A'}
- Monthly Growth: ${data?.monthlyGrowth || copy.monthlyGrowth || 'N/A'}%
- Yearly Growth: ${data?.yearlyGrowth || copy.yearlyGrowth || 'N/A'}%
- Avg Days on Market: ${data?.avgDaysOnMarket || 'N/A'}

TOP GROWING ZIP CODES:
${zipList}

HOOK:
${copy.hook || 'N/A'}

OBJECTIVE:
Create a YouTube Shorts title and description for a Zillow market intelligence channel.

The goal is to maximize:
- Click-through rate
- Watch time
- Subscribers
- Search visibility
- Shorts discovery

TITLE RULES:
Generate ONE title.

Characteristics:
- 45-70 characters
- Curiosity-driven
- Uses real numbers
- High CTR
- Natural language
- Not clickbait

Examples:
NYC Rents Just Jumped 14% in One Month
This ZIP Code Is Outperforming Manhattan
The Housing Market Shift Nobody Expected
Why Investors Are Watching This ZIP Code
New York Rent Prices Are Moving Fast

DESCRIPTION RULES:
Structure:
1. Opening insight
2. Key market data
3. Why it matters
4. Discussion question
5. Follow CTA
6. Hashtags

Use:
- Real numbers from the dataset
- Natural language
- SEO-friendly phrasing
- Housing market terminology
- Real estate investing terminology

Include keywords naturally:
- Zillow
- Real Estate
- Housing Market
- Rental Market
- Property Investing
- Real Estate Investing
- Housing Trends

TONE:
- Smart
- Human
- Data-driven
- Educational
- Conversational

Avoid:
- Corporate language
- Generic AI phrasing
- Excessive emojis
- Hype language
- Buzzwords

HASHTAGS:
Generate 8-12 relevant hashtags.

Mix:
- Real Estate
- Housing Market
- Zillow
- Investing
- Local Market
- City-specific tags

Length: 100-250 words.

Output ONLY:

YouTube Title

(blank line)

YouTube Description with hashtags`,

            x: `Output ONLY the final X post.

Do NOT include:
- "Tweet:"
- "Post:"
- Explanations
- Labels
- Quotation marks
- Markdown headings

Start immediately with the opening line.

You are a top-performing X creator specializing in:
- Real Estate
- Housing Markets
- Investing
- Data Analysis
- Economic Trends

Your job is to transform Zillow market data into highly engaging X posts that maximize:
- Impressions
- Likes
- Replies
- Reposts
- Bookmarks
- Profile visits
- Followers

${marketSection}

OBJECTIVE:
Write a post that feels like a sharp market observation from a real estate analyst.

The reader should think:
- "Interesting..."
- "I didn't know that."
- "That's worth bookmarking."
- "I want to see more of this."

POST STRUCTURE:
1. Strong hook or surprising observation
2. Key data point
3. Why it matters
4. One insight or implication
5. End with a question or discussion starter

WRITING STYLE:
- Human
- Direct
- Intelligent
- Concise
- Data-driven
- Slightly opinionated

Use:
- Real numbers
- Short sentences
- White space
- Strong observations
- Curiosity

Avoid:
- Corporate language
- Generic AI phrases
- Marketing language
- Excessive emojis
- Long paragraphs
- Clickbait

X PSYCHOLOGY:
Posts that perform well often:
- Challenge assumptions
- Highlight unusual trends
- Reveal hidden opportunities
- Point out market inefficiencies
- Ask thoughtful questions

GOOD EXAMPLES:
"NYC rents are up 14.2% in a single month.

That's not the interesting part.

Days on market are falling at the same time.

Demand is rising while inventory isn't keeping up.

What happens if this trend continues through the next quarter?"

Length:
150-280 characters preferred.
Maximum: 600 characters.

Finish with 2-5 highly relevant hashtags.

Output ONLY the final X post.`,
          }

          const prompt = prompts[platform] || prompts.linkedin

          const ollamaResp = await fetch('http://localhost:11434/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              model: 'llama3.1:8b',
              prompt,
              stream: false,
              options: { temperature: 0.8, num_predict: 1024 },
            }),
          })

          const ollamaData: any = await ollamaResp.json()
          let caption = ollamaData.response?.trim() || ''

          // Strip common preamble patterns
          caption = caption.replace(/^(Here(?:'s| is|'s a)|Caption:|Output:|The caption|Below is|Following is|This is).*?\n/gi, '')
          caption = caption.replace(/^\n+/, '')

          // Parse title from caption (LinkedIn format: title\n\ncaption)
          let title = ''
          if (platform === 'linkedin') {
            const parts = caption.split(/\n\n+/)
            if (parts.length >= 2) {
              title = parts[0].replace(/^["']|["']$/g, '').trim()
              caption = parts.slice(1).join('\n\n').trim()
            }
          }

          res.end(JSON.stringify({ ok: true, caption, title }))
        } catch (err: any) {
          res.end(JSON.stringify({ error: err.message }))
        }
      })
    },
  }
}
