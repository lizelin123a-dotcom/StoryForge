import { onBeforeUnmount, ref } from 'vue'
import { api, type SseEvent } from './api'

export function useSSE() {
  const events = ref<SseEvent[]>([])
  const connection = ref<EventSource | null>(null)
  const status = ref<'idle' | 'connecting' | 'connected' | 'error'>('idle')
  const latestEvent = ref<SseEvent | null>(null)

  function connect(onEvent?: (event: SseEvent) => void) {
    disconnect()
    status.value = 'connecting'

    const es = new EventSource(api.events())
    es.onopen = () => {
      status.value = 'connected'
    }
    es.onmessage = (e) => {
      const event = JSON.parse(e.data) as SseEvent
      event.receivedAt = new Date().toLocaleTimeString()
      latestEvent.value = event
      events.value.unshift(event)
      if (events.value.length > 200) events.value.pop()
      onEvent?.(event)
    }
    es.onerror = () => {
      status.value = 'error'
    }
    connection.value = es
  }

  function disconnect() {
    connection.value?.close()
    connection.value = null
    if (status.value !== 'idle') status.value = 'idle'
  }

  onBeforeUnmount(disconnect)

  return { events, connection, status, latestEvent, connect, disconnect }
}
