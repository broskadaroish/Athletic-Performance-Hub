import React, { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Platform,
  Pressable,
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
import { useMobileGetPlayers } from '@workspace/api-client-react';
import type { MobilePlayerSummary } from '@workspace/api-client-react';

const TESTS = [
  {
    id: 'fms',
    name: 'FMS',
    fullName: 'Functional Movement Screen',
    icon: 'activity' as const,
    desc: '7 Bewegungsmuster · Score 0–21',
    route: '/test/fms' as const,
  },
  {
    id: 'sprint',
    name: 'Sprint',
    fullName: 'Linearer Sprint',
    icon: 'zap' as const,
    desc: '10m und 30m Bestzeit',
    route: '/test/sprint' as const,
  },
  {
    id: 'ybalance',
    name: 'Y-Balance',
    fullName: 'Y-Balance Test',
    icon: 'crosshair' as const,
    desc: 'Anterior, PM, PL Reichweiten',
    route: '/test/ybalance' as const,
  },
];

export default function SchnelltestScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const [selectedPlayer, setSelectedPlayer] = useState<MobilePlayerSummary | null>(null);
  const [search, setSearch] = useState('');
  const [step, setStep] = useState<'player' | 'test'>('player');

  const { data, isLoading } = useMobileGetPlayers();

  const players = (data?.players ?? []).filter((p) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return p.name.toLowerCase().includes(q) || (p.mannschaft ?? '').toLowerCase().includes(q);
  });

  const topPad = insets.top + (Platform.OS === 'web' ? 67 : 0);

  if (step === 'test' && selectedPlayer) {
    return (
      <View style={[s.root, { backgroundColor: colors.background }]}>
        <View style={[s.header, { paddingTop: topPad + 16 }]}>
          <Pressable onPress={() => setStep('player')} style={s.back}>
            <Feather name="arrow-left" size={20} color={colors.foreground} />
          </Pressable>
          <View style={s.headerMid}>
            <Text style={[s.headerTitle, { color: colors.foreground }]}>Test wählen</Text>
            <Text style={[s.headerSub, { color: colors.mutedForeground }]}>
              {selectedPlayer.vorname} {selectedPlayer.nachname}
            </Text>
          </View>
        </View>

        <View style={[s.content, { paddingHorizontal: 16 }]}>
          {TESTS.map((test) => (
            <Pressable
              key={test.id}
              style={({ pressed }) => [tc.card(colors), pressed && { opacity: 0.8 }]}
              onPress={() => {
                Haptics.selectionAsync();
                router.push({
                  pathname: test.route,
                  params: { playerId: selectedPlayer.id, playerName: `${selectedPlayer.vorname} ${selectedPlayer.nachname}` },
                });
              }}
            >
              <View style={[tc.iconWrap(colors)]}>
                <Feather name={test.icon} size={22} color={colors.primary} />
              </View>
              <View style={tc.info}>
                <Text style={[tc.name(colors)]}>{test.fullName}</Text>
                <Text style={[tc.desc(colors)]}>{test.desc}</Text>
              </View>
              <Feather name="chevron-right" size={18} color={colors.mutedForeground} />
            </Pressable>
          ))}
        </View>
      </View>
    );
  }

  return (
    <View style={[s.root, { backgroundColor: colors.background }]}>
      <View style={[s.header, { paddingTop: topPad + 16 }]}>
        <Text style={[s.headerTitle, { color: colors.foreground }]}>Schnelltest</Text>
        <Text style={[s.headerSub, { color: colors.mutedForeground }]}>Spieler auswählen</Text>
      </View>

      <View style={[s.searchWrap, { marginHorizontal: 16, marginBottom: 12 }]}>
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

      {isLoading ? (
        <View style={s.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : players.length === 0 ? (
        <View style={s.center}>
          <Feather name="users" size={32} color={colors.mutedForeground} />
          <Text style={[s.emptyText, { color: colors.mutedForeground }]}>
            {search ? 'Keine Treffer' : 'Keine Spieler'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={players}
          keyExtractor={(p) => String(p.id)}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 90 + (Platform.OS === 'web' ? 34 : 0) }}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => (
            <Pressable
              style={({ pressed }) => [pc.item(colors), pressed && { opacity: 0.75 }]}
              onPress={() => {
                Haptics.selectionAsync();
                setSelectedPlayer(item);
                setStep('test');
              }}
            >
              <View style={[pc.av(colors)]}>
                <Text style={[pc.avText(colors)]}>
                  {(item.vorname?.[0] ?? '') + (item.nachname?.[0] ?? '')}
                </Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[pc.name(colors)]}>{item.vorname} {item.nachname}</Text>
                <Text style={[pc.meta(colors)]}>{item.mannschaft ?? 'Kein Team'}</Text>
              </View>
              <Feather name="chevron-right" size={16} color={colors.mutedForeground} />
            </Pressable>
          )}
        />
      )}
    </View>
  );
}

const tc = {
  card: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({
      s: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.card, borderRadius: c.radius, padding: 16, marginBottom: 10, gap: 14, borderWidth: 1, borderColor: c.border },
    }).s,
  iconWrap: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { width: 48, height: 48, borderRadius: 14, backgroundColor: c.primary + '18', alignItems: 'center', justifyContent: 'center' } }).s,
  info: StyleSheet.create({ s: { flex: 1 } }).s,
  name: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { fontSize: 16, fontFamily: 'Inter_600SemiBold', color: c.foreground } }).s,
  desc: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { fontSize: 12, fontFamily: 'Inter_400Regular', color: c.mutedForeground, marginTop: 2 } }).s,
};

const pc = {
  item: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.card, borderRadius: c.radius, padding: 14, marginBottom: 8, gap: 12 } }).s,
  av: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { width: 42, height: 42, borderRadius: 21, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center' } }).s,
  avText: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { fontSize: 15, fontFamily: 'Inter_700Bold', color: c.primary } }).s,
  name: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { fontSize: 15, fontFamily: 'Inter_600SemiBold', color: c.foreground } }).s,
  meta: (c: ReturnType<typeof useColors>) =>
    StyleSheet.create({ s: { fontSize: 12, fontFamily: 'Inter_400Regular', color: c.mutedForeground, marginTop: 2 } }).s,
};

const s = StyleSheet.create({
  root: { flex: 1 },
  header: { paddingHorizontal: 16, paddingBottom: 16 },
  headerTitle: { fontSize: 26, fontFamily: 'Inter_700Bold', letterSpacing: -0.5 },
  headerSub: { fontSize: 14, fontFamily: 'Inter_400Regular', marginTop: 4 },
  back: { marginBottom: 8 },
  headerMid: { gap: 2 },
  content: { flex: 1 },
  searchWrap: { flexDirection: 'row', alignItems: 'center' },
  searchIcon: { position: 'absolute', left: 12, zIndex: 1 },
  search: { flex: 1, borderWidth: 1, borderRadius: 10, paddingLeft: 36, paddingRight: 12, paddingVertical: 10, fontSize: 15, fontFamily: 'Inter_400Regular' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  emptyText: { fontSize: 15, fontFamily: 'Inter_400Regular' },
});
