import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import Input from '@/components/common/Input'
import { settingsApi } from '@/lib/api'

/** Admin setting: the WatchBase API key used by "Look up" on the watch form */
export default function WatchBaseKeyCard() {
  const queryClient = useQueryClient()
  const [key, setKey] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const { data: status } = useQuery({
    queryKey: ['settings', 'watchbase-key'],
    queryFn: settingsApi.getWatchBaseKey,
  })

  const done = (text: string) => () => {
    setKey('')
    setMessage(text)
    queryClient.invalidateQueries({ queryKey: ['settings', 'watchbase-key'] })
  }
  const failed = () => setMessage('Could not save the key. Check it has no spaces.')
  const save = useMutation({
    mutationFn: settingsApi.setWatchBaseKey,
    onSuccess: done('Key saved.'),
    onError: failed,
  })
  const clear = useMutation({
    mutationFn: settingsApi.clearWatchBaseKey,
    onSuccess: done('Key removed. Look up now shows links only.'),
    onError: failed,
  })

  return (
    <Card className="p-6 space-y-4">
      <div>
        <h2 className="text-xl font-light tracking-wide text-foreground">Reference look-up</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          With a{' '}
          <a
            href="https://watchbase.com/manuals/datafeed"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-700 underline"
          >
            WatchBase Data Feed
          </a>{' '}
          API key, "Look up" on the watch form fills specs from the reference number. WatchBase
          charges per watch (about US $0.30); answers are kept for 90 days, so looking up the same
          reference again is free. Without a key, Look up shows search links instead.
        </p>
      </div>

      <p className="text-sm text-foreground" role="status">
        Status:{' '}
        <strong>
          {status?.configured
            ? status.from_environment
              ? 'set by WATCHBASE_API_KEY on the server'
              : 'key saved'
            : 'no key (links only)'}
        </strong>
      </p>

      {status?.from_environment ? (
        <p className="text-sm text-muted-foreground">
          To change it, change WATCHBASE_API_KEY and restart the container.
        </p>
      ) : (
        <form
          className="flex flex-col sm:flex-row gap-3 sm:items-end"
          onSubmit={(e) => {
            e.preventDefault()
            if (key.trim()) save.mutate(key.trim())
          }}
        >
          <div className="flex-1">
            <Input
              id="watchbase-key"
              label={status?.configured ? 'Replace the API key' : 'WatchBase API key'}
              type="password"
              autoComplete="off"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="Paste the key from your WatchBase account"
            />
          </div>
          <Button type="submit" disabled={!key.trim() || save.isPending}>
            {save.isPending ? 'Saving...' : 'Save key'}
          </Button>
          {status?.configured && (
            <Button
              type="button"
              variant="secondary"
              onClick={() => clear.mutate()}
              disabled={clear.isPending}
            >
              Remove key
            </Button>
          )}
        </form>
      )}
      {message && <p className="text-sm text-foreground">{message}</p>}
      <p className="text-xs text-muted-foreground">
        The key is stored on the server only and is never shown again or sent to browsers.
      </p>
    </Card>
  )
}
