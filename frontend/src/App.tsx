import { useEffect, useState } from 'react'
import type { Item } from './api'
import { listItems, createItem, updateItem, deleteItem } from './api'

export default function App() {
  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Item | null>(null)
  const [formName, setFormName] = useState('')
  const [formDesc, setFormDesc] = useState('')

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const { items: list } = await listItems()
      setItems(list)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formName.trim()) return
    setError(null)
    try {
      await createItem(formName.trim(), formDesc.trim() || undefined)
      setFormName('')
      setFormDesc('')
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed')
    }
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editing || !formName.trim()) return
    setError(null)
    try {
      await updateItem(editing.id, formName.trim(), formDesc.trim() || undefined)
      setEditing(null)
      setFormName('')
      setFormDesc('')
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Update failed')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this item?')) return
    setError(null)
    try {
      await deleteItem(id)
      if (editing?.id === id) setEditing(null)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  const startEdit = (item: Item) => {
    setEditing(item)
    setFormName(item.name)
    setFormDesc(item.description ?? '')
  }

  const cancelEdit = () => {
    setEditing(null)
    setFormName('')
    setFormDesc('')
  }

  return (
    <div>
      <h1 style={{ marginBottom: '0.5rem' }}>Items</h1>
      <p style={{ color: '#71717a', marginBottom: '1.5rem' }}>CRUD with FastAPI and DynamoDB</p>

      <form
        onSubmit={editing ? handleUpdate : handleCreate}
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          marginBottom: '1.5rem',
          padding: '1rem',
          background: '#18181b',
          borderRadius: '8px',
        }}
      >
        <input
          type="text"
          placeholder="Name"
          value={formName}
          onChange={(e) => setFormName(e.target.value)}
          required
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #3f3f46', background: '#0f0f12', color: '#e4e4e7' }}
        />
        <textarea
          placeholder="Description"
          value={formDesc}
          onChange={(e) => setFormDesc(e.target.value)}
          rows={2}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #3f3f46', background: '#0f0f12', color: '#e4e4e7', resize: 'vertical' }}
        />
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="submit" style={{ padding: '0.5rem 1rem', borderRadius: '4px', border: 'none', background: '#3b82f6', color: 'white', cursor: 'pointer' }}>
            {editing ? 'Update' : 'Create'}
          </button>
          {editing && (
            <button type="button" onClick={cancelEdit} style={{ padding: '0.5rem 1rem', borderRadius: '4px', border: '1px solid #3f3f46', background: 'transparent', color: '#e4e4e7', cursor: 'pointer' }}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}
      {loading && <p style={{ color: '#71717a' }}>Loading…</p>}
      {!loading && items.length === 0 && !error && <p style={{ color: '#71717a' }}>No items yet. Create one above.</p>}
      {!loading && items.length > 0 && (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {items.map((item) => (
            <li
              key={item.id}
              style={{
                padding: '1rem',
                marginBottom: '0.5rem',
                background: '#18181b',
                borderRadius: '8px',
                border: '1px solid #27272a',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                <div>
                  <strong>{item.name}</strong>
                  {item.description && <p style={{ margin: '0.25rem 0 0', color: '#a1a1aa', fontSize: '0.9rem' }}>{item.description}</p>}
                  <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: '#71717a' }}>{item.id}</p>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button onClick={() => startEdit(item)} style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem', borderRadius: '4px', border: '1px solid #3f3f46', background: 'transparent', color: '#e4e4e7', cursor: 'pointer' }}>Edit</button>
                  <button onClick={() => handleDelete(item.id)} style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem', borderRadius: '4px', border: 'none', background: '#7f1d1d', color: 'white', cursor: 'pointer' }}>Delete</button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
