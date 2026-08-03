import React, { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Platform,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useColors } from '@/hooks/useColors';
import { useAuth } from '@/contexts/AuthContext';
import { useMobileGetPlayers } from '@workspace/api-client-react';
import type { MobilePlayerSummary } from '@workspace/api-client-react';

function ScoreBadge({ score }: { score: number | null | undefined }) {
  const colors = useColors();
  if (score == null) {
    return (
      <View style={[badge.wrap, { backgroundColor: colors.muted }]}>
        <Text style={[badge.text, { color: colors.mutedForeground }]}>—</Text>
      </View>
    );
  }
  const bg =
    score >= 75
      ? colors.primary
      : score >= 50
      ? '#F59E0B'
      : colors.destructive;
  return (
    <View style={[badge.wrap, { backgroundColor: bg + '22' }]}>
      <Text style={[badge.text, { color: bg }]}>{score}</Text>
    </View>
  );
}

const badge = StyleSheet.create({
  wrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontSize: 14,
    fontFamily: 'Inter_700Bold',
  },
});

function PlayerCard({ player }: { player: MobilePlayerSummary }) {
  const colors = useColors();
  return (
    <Pressable
      style={({ pressed }) => [pc.card(colors), pressed && { opacity: 0.75 }]}
      onPress={() => {
        Haptics.selectionAsync();
        router.push(`/player/${player.id}`);
      }}
    >
      <View style={pc.avatar(colors)}>
        <Text style={pc.avatarText(colors)}>
          {(player.vorname?.[0] ?? '') + (player.nachname?.[0] ?? '')}
        </Text>
      </View>
      <View style={pc.info}>
        <Text style={pc.name(colors)} numberOfLines={1}>
          {player.vorname} {player.nachname}
        </Text>
        <Text style={pc.meta(colors)} numberOfLines={1}>
          {[player.mannschaft, player.altersklasse].filter(Boolean).join(' · ') || 'Kein Team'}
        </Text>
      </View>
      <ScoreBadge score={player.score} />
      <Feather name="chevron-right" size={16} color={colors.mutedForeground} style={{ marginLeft: 4 }} />
    </Pressable>
  );
}

const pc = {
  card: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.card, borderRadius: c.radius, padding: 14, marginBottom: 8, gap: 12 } }).s,
  avatar: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { width: 42, height: 42, borderRadius: 21, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center' } }).s,
  avatarText: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { fontSize: 15, fontFamily: 'Inter_700Bold', color: c.primary } }).s,
  info: StyleSheet.create({ s: { flex: 1, minWidth: 0 } }).s,
  name: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { fontSize: 15, fontFamily: 'Inter_600SemiBold', color: c.foreground } }).s,
  meta: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { fontSize: 12, fontFamily: 'Inter_400Regular', color: c.mutedForeground, marginTop: 2 } }).s,
};

export default function PlayersScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { user } = useAuth();
  const [search, setSearch] = useState('');

  const { data, isLoading, isError, refetch, isFetching } = useMobileGetPlayers();

  const players = (data?.players ?? []).filter((p) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      (p.mannschaft ?? '').toLowerCase().includes(q) ||
      (p.altersklasse ?? '').toLowerCase().includes(q)
    );
  });

  // Group by team
  const teams = [...new Set((data?.players ?? []).map((p) => p.mannschaft ?? 'Kein Team'))].sort();
  const [activeTeam, setActiveTeam] = useState<string | null>(null);

  const filtered = activeTeam
    ? players.filter((p) => (p.mannschaft ?? 'Kein Team') === activeTeam)
    : players;

  const topPad = insets.top + (Platform.OS === 'web' ? 67 : 0);

  return (
    <View style={[s.root, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 16 }]}>
        <View>
          <Text style={[s.greeting, { color: colors.mutedForeground }]}>Willkommen</Text>
          <Text style={[s.headerTitle, { color: colors.foreground }]}>
            {user?.vorname ?? 'Trainer'}
          </Text>
        </View>
        <View style={[s.badge, { backgroundColor: colors.secondary }]}>
          <Text style={[s.badgeText, { color: colors.primary }]}>
            {data?.players.length ?? 0}
          </Text>
        </View>
      </View>

      {/* Search */}
      <View style={[s.searchWrap, { marginHorizontal: 16, marginBottom: 8 }]}>
        <Feather name="search" size={16} color={colors.mutedForeground} style={s.searchIcon} />
        <TextInput
          style={[s.search, { backgroundColor: colors.card, color: colors.foreground, borderColor: colors.border }]}
          value={search}
          onChangeText={setSearch}
          placeholder="Spieler suchen…"
          placeholderTextColor={colors.mutedForeground}
          clearButtonMode="while-editing"
        />
      </View>

      {/* Team filter chips */}
      {teams.length > 1 && (
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={[null, ...teams]}
          keyExtractor={(t) => t ?? '__all'}
          style={{ flexGrow: 0, marginBottom: 8 }}
          contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}
          renderItem={({ item }) => (
            <Pressable
              style={[
                s.chip,
                {
                  backgroundColor: activeTeam === item ? colors.primary : colors.card,
                  borderColor: activeTeam === item ? colors.primary : colors.border,
                },
              ]}
              onPress={() => setActiveTeam(item)}
            >
              <Text
                style={[
                  s.chipText,
                  { color: activeTeam === item ? colors.primaryForeground : colors.foreground },
                ]}
              >
                {item ?? 'Alle'}
              </Text>
            </Pressable>
          )}
        />
      )}

      {/* List */}
      {isLoading ? (
        <View style={s.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : isError ? (
        <View style={s.center}>
          <Feather name="wifi-off" size={32} color={colors.mutedForeground} />
          <Text style={[s.emptyText, { color: colors.mutedForeground }]}>Verbindungsfehler</Text>
          <Pressable style={[s.retryBtn, { borderColor: colors.border }]} onPress={() => refetch()}>
            <Text style={[s.retryText, { color: colors.primary }]}>Erneut versuchen</Text>
          </Pressable>
        </View>
      ) : filtered.length === 0 ? (
        <View style={s.center}>
          <Feather name="users" size={32} color={colors.mutedForeground} />
          <Text style={[s.emptyText, { color: colors.mutedForeground }]}>
            {search ? 'Keine Treffer' : 'Noch keine Spieler'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(p) => String(p.id)}
          renderItem={({ item }) => <PlayerCard player={item} />}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 90 + (Platform.OS === 'web' ? 34 : 0) }}
          showsVerticalScrollIndicator={false}
          scrollEnabled={filtered.length > 0}
          refreshControl={
            <RefreshControl
              refreshing={isFetching && !isLoading}
              onRefresh={refetch}
              tintColor={colors.primary}
            />
          }
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: { paddingHorizontal: 16, paddingBottom: 16, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' },
  greeting: { fontSize: 13, fontFamily: 'Inter_400Regular' },
  headerTitle: { fontSize: 26, fontFamily: 'Inter_700Bold', letterSpacing: -0.5, marginTop: 2 },
  badge: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  badgeText: { fontSize: 14, fontFamily: 'Inter_700Bold' },
  searchWrap: { flexDirection: 'row', alignItems: 'center' },
  searchIcon: { position: 'absolute', left: 12, zIndex: 1 },
  search: { flex: 1, borderWidth: 1, borderRadius: 10, paddingLeft: 36, paddingRight: 12, paddingVertical: 10, fontSize: 15, fontFamily: 'Inter_400Regular' },
  chip: { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20, borderWidth: 1 },
  chipText: { fontSize: 13, fontFamily: 'Inter_500Medium' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, paddingBottom: 80 },
  emptyText: { fontSize: 15, fontFamily: 'Inter_400Regular' },
  retryBtn: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 16, paddingVertical: 8 },
  retryText: { fontSize: 14, fontFamily: 'Inter_500Medium' },
});
