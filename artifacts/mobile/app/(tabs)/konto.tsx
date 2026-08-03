import React, { useEffect, useState } from 'react';
import { Platform, Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useColors } from '@/hooks/useColors';
import { useAuth } from '@/contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

function getBaseUrl(): string {
  const domain = process.env['EXPO_PUBLIC_DOMAIN'];
  if (domain) return `https://${domain}`;
  return '';
}

export default function KontoScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { user, token, logout } = useAuth();
  const queryClient = useQueryClient();
  const topPad = insets.top + (Platform.OS === 'web' ? 67 : 0);

  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [loadingToggle, setLoadingToggle] = useState(false);

  // Load current notification setting from server
  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const res = await fetch(`${getBaseUrl()}/api/mobile/notifications/settings`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json() as { enabled: boolean };
          setNotificationsEnabled(data.enabled);
        }
      } catch {
        // ignore — keep default true
      }
    })();
  }, [token]);

  const handleToggleNotifications = async (value: boolean) => {
    if (!token || loadingToggle) return;
    setLoadingToggle(true);
    setNotificationsEnabled(value); // optimistic update
    try {
      const res = await fetch(`${getBaseUrl()}/api/mobile/notifications/settings`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ enabled: value }),
      });
      if (!res.ok) {
        // Revert optimistic update on server error
        setNotificationsEnabled(!value);
      }
    } catch {
      // Revert on network failure
      setNotificationsEnabled(!value);
    } finally {
      setLoadingToggle(false);
    }
  };

  const handleLogout = async () => {
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    queryClient.clear();
    await logout();
  };

  const initials = ((user?.vorname?.[0] ?? '') + (user?.nachname?.[0] ?? '')).toUpperCase();

  return (
    <View style={[s.root, { backgroundColor: colors.background }]}>
      <View style={[s.header, { paddingTop: topPad + 16 }]}>
        <Text style={[s.title, { color: colors.foreground }]}>Konto</Text>
      </View>

      {/* Avatar */}
      <View style={s.avatarSection}>
        <View style={[s.avatar, { backgroundColor: colors.primary + '22' }]}>
          <Text style={[s.avatarText, { color: colors.primary }]}>{initials || '?'}</Text>
        </View>
        <Text style={[s.name, { color: colors.foreground }]}>
          {user?.vorname} {user?.nachname}
        </Text>
        <Text style={[s.email, { color: colors.mutedForeground }]}>{user?.email}</Text>
        {user?.verein_name && (
          <View style={[s.club, { backgroundColor: colors.secondary }]}>
            <Feather name="shield" size={12} color={colors.primary} />
            <Text style={[s.clubText, { color: colors.primary }]}>{user.verein_name}</Text>
          </View>
        )}
      </View>

      {/* Info rows */}
      <View style={[s.section, { marginHorizontal: 16 }]}>
        <View style={[s.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <InfoRow icon="user" label="Rolle" value={user?.rolle ?? '—'} colors={colors} />
          {user?.verein_name && (
            <>
              <View style={[s.divider, { backgroundColor: colors.border }]} />
              <InfoRow icon="home" label="Verein" value={user.verein_name} colors={colors} />
            </>
          )}
        </View>
      </View>

      {/* Notification setting */}
      {Platform.OS !== 'web' && (
        <View style={[s.section, { marginHorizontal: 16, marginTop: 12 }]}>
          <View style={[s.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
            <View style={nr.row}>
              <Feather name="bell" size={16} color={colors.mutedForeground} />
              <Text style={[nr.label, { color: colors.mutedForeground }]}>Benachrichtigungen</Text>
              <Switch
                value={notificationsEnabled}
                onValueChange={handleToggleNotifications}
                disabled={loadingToggle}
                trackColor={{ false: colors.border, true: colors.primary + '66' }}
                thumbColor={notificationsEnabled ? colors.primary : colors.mutedForeground}
              />
            </View>
            <View style={[s.divider, { backgroundColor: colors.border }]} />
            <View style={nr.hint}>
              <Text style={[nr.hintText, { color: colors.mutedForeground }]}>
                {notificationsEnabled
                  ? 'Du erhältst Push-Benachrichtigungen bei Spieler-Updates.'
                  : 'Push-Benachrichtigungen sind deaktiviert.'}
              </Text>
            </View>
          </View>
        </View>
      )}

      <View style={{ flex: 1 }} />

      {/* Logout */}
      <View style={[s.logoutWrap, { marginHorizontal: 16, marginBottom: insets.bottom + 90 + (Platform.OS === 'web' ? 34 : 0) }]}>
        <Pressable
          style={({ pressed }) => [s.logoutBtn, { borderColor: colors.destructive, opacity: pressed ? 0.7 : 1 }]}
          onPress={handleLogout}
        >
          <Feather name="log-out" size={18} color={colors.destructive} />
          <Text style={[s.logoutText, { color: colors.destructive }]}>Abmelden</Text>
        </Pressable>
      </View>
    </View>
  );
}

function InfoRow({ icon, label, value, colors }: { icon: any; label: string; value: string; colors: ReturnType<typeof useColors> }) {
  return (
    <View style={ir.row}>
      <Feather name={icon} size={16} color={colors.mutedForeground} />
      <Text style={[ir.label, { color: colors.mutedForeground }]}>{label}</Text>
      <Text style={[ir.value, { color: colors.foreground }]} numberOfLines={1}>{value}</Text>
    </View>
  );
}

const ir = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 14, paddingHorizontal: 16 },
  label: { fontSize: 14, fontFamily: 'Inter_400Regular', flex: 0, minWidth: 60 },
  value: { fontSize: 14, fontFamily: 'Inter_500Medium', flex: 1, textAlign: 'right' },
});

const nr = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 14, paddingHorizontal: 16 },
  label: { fontSize: 14, fontFamily: 'Inter_400Regular', flex: 1 },
  hint: { paddingHorizontal: 16, paddingBottom: 12, paddingTop: 4 },
  hintText: { fontSize: 12, fontFamily: 'Inter_400Regular', lineHeight: 18 },
});

const s = StyleSheet.create({
  root: { flex: 1 },
  header: { paddingHorizontal: 16, paddingBottom: 8 },
  title: { fontSize: 26, fontFamily: 'Inter_700Bold', letterSpacing: -0.5 },
  avatarSection: { alignItems: 'center', paddingVertical: 28, gap: 6 },
  avatar: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
  avatarText: { fontSize: 28, fontFamily: 'Inter_700Bold' },
  name: { fontSize: 20, fontFamily: 'Inter_700Bold' },
  email: { fontSize: 14, fontFamily: 'Inter_400Regular' },
  club: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20, marginTop: 4 },
  clubText: { fontSize: 13, fontFamily: 'Inter_500Medium' },
  section: {},
  card: { borderWidth: 1, borderRadius: 12 },
  divider: { height: 1, marginHorizontal: 16 },
  logoutWrap: {},
  logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, borderWidth: 1.5, borderRadius: 12, paddingVertical: 14 },
  logoutText: { fontSize: 16, fontFamily: 'Inter_600SemiBold' },
});
