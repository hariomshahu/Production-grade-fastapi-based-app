/**
 * API client for Items CRUD.
 * In dev Vite proxies /items to backend; in prod use same origin (Nginx proxies).
 */
const getBase = () => {
  const env = import.meta.env?.VITE_API_URL
  if (env) return env.replace(/\/$/, '')
  return '' // same origin
}

export interface Item {
  id: string
  name: string
  description: string | null
  created_at: string
}

export async function listItems(limit = 100, lastId?: string): Promise<{ items: Item[]; lastEvaluatedKey?: string }> {
  const url = new URL(`${getBase()}/items`)
  url.searchParams.set('limit', String(limit))
  if (lastId) url.searchParams.set('lastEvaluatedKey', lastId)
  const r = await fetch(url.toString())
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getItem(id: string): Promise<Item> {
  const r = await fetch(`${getBase()}/items/${id}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function createItem(name: string, description?: string): Promise<Item> {
  const r = await fetch(`${getBase()}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description: description ?? null }),
  })
  if (!r.ok) {
    const text = await r.text()
    try {
      const j = JSON.parse(text)
      throw new Error(j.detail || text)
    } catch (e) {
      if (e instanceof Error && e.message !== text) throw e
      throw new Error(text || `Create failed (${r.status})`)
    }
  }
  return r.json()
}

export async function updateItem(id: string, name: string, description?: string): Promise<Item> {
  const r = await fetch(`${getBase()}/items/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description: description ?? null }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function deleteItem(id: string): Promise<void> {
  const r = await fetch(`${getBase()}/items/${id}`, { method: 'DELETE' })
  if (!r.ok) throw new Error(await r.text())
}
