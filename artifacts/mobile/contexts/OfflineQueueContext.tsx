/**
 * Offline queue for test submissions.
 *
 * When the device has no network connection, test results are stored locally in
 * AsyncStorage and automatically replayed the next time the app comes to the
 * foreground or the periodic retry fires.
 */
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppState, AppStateStatus } from 'react-native';
import { useQueryClient } from '@tanstack/react-query';
import {
  mobileSubmitFms,
  mobileSubmitSprint,
  mobileSubmitYbalance,
  getMobileGetPlayersQueryKey,
  getMobileGetPlayerQueryKey,
} from '@workspace/api-client-react';
import type {
  MobileFmsRequest,
  MobileSprintRequest,
  MobileYbalanceRequest,
} from '@workspace/api-client-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type QueueItemType = 'fms' | 'sprint' | 'ybalance';

type FmsData = MobileFmsRequest;
type SprintData = MobileSprintRequest;
type YbalanceData = MobileYbalanceRequest;

export interface QueueItem {
  id: string;
  type: QueueItemType;
  playerId: number;
  playerName: string;
  data: FmsData | SprintData | YbalanceData;
  queuedAt: string;
}

interface OfflineQueueContextValue {
  /** Number of test results not yet synced to the server. */
  pendingCount: number;
  /** Append a new item to the queue (called when a save fails due to no network). */
  enqueue: (item: Omit<QueueItem, 'id' | 'queuedAt'>) => Promise<void>;
  /** Attempt to submit all queued items to the server immediately. */
  flushQueue: () => Promise<void>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const QUEUE_KEY = 'athletik_offline_queue';

/** Returns true when the error looks like a network failure (no response). */
export function isNetworkError(err: unknown): boolean {
  if (err instanceof TypeError) return true;
  if (
    err instanceof Error &&
    (err.message.includes('Network request failed') ||
      err.message.includes('Failed to fetch') ||
      err.message.includes('network') ||
      err.message.includes('Network'))
  ) {
    return true;
  }
  return false;
}

async function readQueue(): Promise<QueueItem[]> {
  try {
    const raw = await AsyncStorage.getItem(QUEUE_KEY);
    return raw ? (JSON.parse(raw) as QueueItem[]) : [];
  } catch {
    return [];
  }
}

async function writeQueue(items: QueueItem[]): Promise<void> {
  try {
    await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(items));
  } catch {
    // Ignore storage errors — worst case items are lost on restart
  }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const OfflineQueueContext = createContext<OfflineQueueContextValue>({
  pendingCount: 0,
  enqueue: async () => {},
  flushQueue: async () => {},
});

export function OfflineQueueProvider({ children }: { children: React.ReactNode }) {
  const [pendingCount, setPendingCount] = useState(0);
  const queryClient = useQueryClient();
  const isFlushing = useRef(false);

  // Load initial count from storage
  useEffect(() => {
    readQueue().then((items) => setPendingCount(items.length));
  }, []);

  const enqueue = useCallback(async (item: Omit<QueueItem, 'id' | 'queuedAt'>) => {
    const newItem: QueueItem = {
      ...item,
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      queuedAt: new Date().toISOString(),
    };
    const current = await readQueue();
    const updated = [...current, newItem];
    await writeQueue(updated);
    setPendingCount(updated.length);
  }, []);

  const flushQueue = useCallback(async () => {
    if (isFlushing.current) return;
    isFlushing.current = true;
    try {
      const items = await readQueue();
      if (items.length === 0) return;

      const remaining: QueueItem[] = [];

      for (const item of items) {
        try {
          if (item.type === 'fms') {
            await mobileSubmitFms(item.playerId, item.data as FmsData);
          } else if (item.type === 'sprint') {
            await mobileSubmitSprint(item.playerId, item.data as SprintData);
          } else if (item.type === 'ybalance') {
            await mobileSubmitYbalance(item.playerId, item.data as YbalanceData);
          }
          // Successfully synced — invalidate player cache so next open shows fresh data
          queryClient.invalidateQueries({ queryKey: getMobileGetPlayersQueryKey() });
          queryClient.invalidateQueries({
            queryKey: getMobileGetPlayerQueryKey(item.playerId),
          });
        } catch (err) {
          if (isNetworkError(err)) {
            // Still no connection — keep item for next attempt
            remaining.push(item);
          }
          // Server/validation error (4xx/5xx) — discard; retrying won't help
        }
      }

      await writeQueue(remaining);
      setPendingCount(remaining.length);
    } finally {
      isFlushing.current = false;
    }
  }, [queryClient]);

  // Auto-flush when app returns to foreground
  useEffect(() => {
    const sub = AppState.addEventListener('change', (nextState: AppStateStatus) => {
      if (nextState === 'active') {
        flushQueue();
      }
    });
    return () => sub.remove();
  }, [flushQueue]);

  // Periodic retry every 30 s while items are pending
  useEffect(() => {
    if (pendingCount === 0) return;
    const timer = setInterval(flushQueue, 30_000);
    return () => clearInterval(timer);
  }, [pendingCount, flushQueue]);

  return (
    <OfflineQueueContext.Provider value={{ pendingCount, enqueue, flushQueue }}>
      {children}
    </OfflineQueueContext.Provider>
  );
}

export function useOfflineQueue() {
  return useContext(OfflineQueueContext);
}
