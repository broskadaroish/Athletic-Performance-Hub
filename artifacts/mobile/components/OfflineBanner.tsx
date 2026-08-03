import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useOfflineQueue } from '@/contexts/OfflineQueueContext';

/**
 * Shows a yellow banner when there are pending test results waiting to be
 * synced to the server.  Renders nothing when the queue is empty.
 */
export function OfflineBanner() {
  const { pendingCount } = useOfflineQueue();
  if (pendingCount === 0) return null;

  return (
    <View style={s.banner}>
      <Feather name="wifi-off" size={14} color="#B45309" />
      <Text style={s.text}>
        {pendingCount === 1
          ? '1 Test offline gespeichert — wird synchronisiert sobald Netz verfügbar'
          : `${pendingCount} Tests offline gespeichert — werden synchronisiert sobald Netz verfügbar`}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#F59E0B60',
    backgroundColor: '#FEF3C7',
    marginHorizontal: 16,
    marginBottom: 8,
  },
  text: {
    flex: 1,
    fontSize: 12,
    fontFamily: 'Inter_500Medium',
    lineHeight: 17,
    color: '#92400E',
  },
});
