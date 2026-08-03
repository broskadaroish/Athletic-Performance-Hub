import React from 'react';
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useColors } from '@/hooks/useColors';
import { useMobileGetPlayer } from '@workspace/api-client-react';

function ScoreRing({ score }: { score: number | null | undefined }) {
  const colors = useColors();
  const val = score ?? 0;
  const color = val >= 75 ? colors.primary : val >= 50 ? '#F59E0B' : colors.destructive;
  return (
    <View style={sr.wrap}>
      <View style={[sr.outer, { borderColor: color + '30' }]}>
        <View style={[sr.inner, { backgroundColor: colors.card }]}>
          <Text style={[sr.score, { color }]}>{score != null ? score : '—'}</Text>
          <Text style={[sr.label, { color: colors.mutedForeground }]}>/ 100</Text>
        </View>
      </View>
      <Text style={[sr.tag, { color, backgroundColor: color + '18' }]}>
        {val >= 75 ? 'Hervorragend' : val >= 60 ? 'Gut' : val >= 45 ? 'Durchschnittlich' : score == null ? 'Kein Score' : 'Verbesserungsbedarf'}
      </Text>
    </View>
  );
}
const sr = StyleSheet.create({
  wrap: { alignItems: 'center', gap: 10 },
  outer: { width: 140, height: 140, borderRadius: 70, borderWidth: 6, alignItems: 'center', justifyContent: 'center' },
  inner: { width: 116, height: 116, borderRadius: 58, alignItems: 'center', justifyContent: 'center' },
  score: { fontSize: 42, fontFamily: 'Inter_700Bold', letterSpacing: -1 },
  label: { fontSize: 13, fontFamily: 'Inter_400Regular', marginTop: -4 },
  tag: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 20, fontSize: 13, fontFamily: 'Inter_600SemiBold' },
});

function TestCard({ title, icon, datum, children }: { title: string; icon: any; datum?: string | null; children: React.ReactNode }) {
  const colors = useColors();
  return (
    <View style={[tc.wrap, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <View style={tc.head}>
        <View style={[tc.iconWrap, { backgroundColor: colors.primary + '18' }]}>
          <Feather name={icon} size={16} color={colors.primary} />
        </View>
        <Text style={[tc.title, { color: colors.foreground }]}>{title}</Text>
        {datum && <Text style={[tc.datum, { color: colors.mutedForeground }]}>{datum}</Text>}
      </View>
      {children}
    </View>
  );
}
const tc = StyleSheet.create({
  wrap: { borderRadius: 12, borderWidth: 1, padding: 16, marginBottom: 10 },
  head: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 },
  iconWrap: { width: 32, height: 32, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 15, fontFamily: 'Inter_600SemiBold', flex: 1 },
  datum: { fontSize: 12, fontFamily: 'Inter_400Regular' },
});

function Metric({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  const colors = useColors();
  return (
    <View style={[mm.wrap, { backgroundColor: highlight ? colors.primary + '12' : colors.secondary }]}>
      <Text style={[mm.value, { color: highlight ? colors.primary : colors.foreground }]}>{value}</Text>
      <Text style={[mm.label, { color: colors.mutedForeground }]}>{label}</Text>
    </View>
  );
}
const mm = StyleSheet.create({
  wrap: { flex: 1, borderRadius: 8, padding: 10, alignItems: 'center' },
  value: { fontSize: 18, fontFamily: 'Inter_700Bold' },
  label: { fontSize: 11, fontFamily: 'Inter_400Regular', marginTop: 2, textAlign: 'center' },
});

export default function PlayerDetailScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { id } = useLocalSearchParams<{ id: string }>();
  const playerId = parseInt(id ?? '0', 10);

  const { data, isLoading, isError, refetch } = useMobileGetPlayer(playerId, {
    query: { enabled: !!playerId },
  });

  const topPad = insets.top + (Platform.OS === 'web' ? 67 : 0);

  if (isLoading) {
    return (
      <View style={[s.root, { backgroundColor: colors.background, paddingTop: topPad + 60 }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (isError || !data) {
    return (
      <View style={[s.root, { backgroundColor: colors.background, paddingTop: topPad + 60 }]}>
        <Feather name="alert-circle" size={32} color={colors.mutedForeground} />
        <Text style={[s.errText, { color: colors.mutedForeground }]}>Spieler nicht gefunden</Text>
        <Pressable style={[s.retryBtn, { borderColor: colors.border }]} onPress={() => refetch()}>
          <Text style={[s.retryText, { color: colors.primary }]}>Erneut versuchen</Text>
        </Pressable>
      </View>
    );
  }

  const { player, tests } = data;
  const score = data.score;

  return (
    <ScrollView
      style={[s.root, { backgroundColor: colors.background }]}
      contentContainerStyle={{ paddingBottom: insets.bottom + 30 + (Platform.OS === 'web' ? 34 : 0) }}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero */}
      <View style={[s.hero, { paddingTop: topPad + 60, paddingHorizontal: 24 }]}>
        <View style={[s.avatarWrap, { backgroundColor: colors.secondary }]}>
          <Text style={[s.avatarText, { color: colors.primary }]}>
            {(player.vorname?.[0] ?? '') + (player.nachname?.[0] ?? '')}
          </Text>
        </View>
        <Text style={[s.playerName, { color: colors.foreground }]}>
          {player.vorname} {player.nachname}
        </Text>
        {(player.mannschaft || player.altersklasse) && (
          <Text style={[s.playerMeta, { color: colors.mutedForeground }]}>
            {[player.mannschaft, player.altersklasse].filter(Boolean).join(' · ')}
          </Text>
        )}
        <View style={{ marginTop: 20 }}>
          <ScoreRing score={score} />
        </View>
      </View>

      {/* Quick test buttons */}
      <View style={[s.actions, { marginHorizontal: 16, marginTop: 24 }]}>
        <Text style={[s.sectionTitle, { color: colors.mutedForeground }]}>NEUER TEST</Text>
        <View style={s.actionsRow}>
          {[
            { label: 'FMS', icon: 'activity', route: '/test/fms' as const },
            { label: 'Sprint', icon: 'zap', route: '/test/sprint' as const },
            { label: 'Y-Balance', icon: 'crosshair', route: '/test/ybalance' as const },
          ].map((t) => (
            <Pressable
              key={t.route}
              style={({ pressed }) => [
                s.actionBtn,
                { backgroundColor: colors.card, borderColor: colors.border, opacity: pressed ? 0.75 : 1 },
              ]}
              onPress={() => {
                Haptics.selectionAsync();
                router.push({
                  pathname: t.route,
                  params: { playerId, playerName: `${player.vorname} ${player.nachname}` },
                });
              }}
            >
              <Feather name={t.icon as any} size={18} color={colors.primary} />
              <Text style={[s.actionLabel, { color: colors.foreground }]}>{t.label}</Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* Test results */}
      <View style={[s.results, { marginHorizontal: 16, marginTop: 20 }]}>
        <Text style={[s.sectionTitle, { color: colors.mutedForeground, marginBottom: 10 }]}>LETZTE TESTS</Text>

        {tests.fms ? (
          <TestCard title="FMS" icon="activity" datum={tests.fms.datum}>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <Metric label="Score" value={`${tests.fms.score}/21`} highlight />
              <Metric label="Bewertung" value={tests.fms.bewertung ?? '—'} />
              <Metric label="Asymmetrie" value={tests.fms.asymmetrie?.includes('Keine') ? '—' : '⚠️'} />
            </View>
          </TestCard>
        ) : (
          <NoTest title="FMS" icon="activity" colors={colors} />
        )}

        {tests.sprint ? (
          <TestCard title="Sprint" icon="zap" datum={tests.sprint.datum}>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              {tests.sprint.beste_10m != null && (
                <Metric label="10m" value={`${tests.sprint.beste_10m.toFixed(2)}s`} highlight />
              )}
              {tests.sprint.beste_30m != null && (
                <Metric label="30m" value={`${tests.sprint.beste_30m.toFixed(2)}s`} />
              )}
              {tests.sprint.bewertung_10m && (
                <Metric label="Rating" value={tests.sprint.bewertung_10m} />
              )}
            </View>
          </TestCard>
        ) : (
          <NoTest title="Sprint" icon="zap" colors={colors} />
        )}

        {tests.ybalance ? (
          <TestCard title="Y-Balance" icon="crosshair" datum={tests.ybalance.datum}>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <Metric label="Rechts" value={`${tests.ybalance.composite_rechts.toFixed(1)}`} highlight />
              <Metric label="Links" value={`${tests.ybalance.composite_links.toFixed(1)}`} />
              <Metric label="Asymm." value={tests.ybalance.asymmetrie?.includes('Keine') ? 'OK' : '⚠️'} />
            </View>
          </TestCard>
        ) : (
          <NoTest title="Y-Balance" icon="crosshair" colors={colors} />
        )}
      </View>
    </ScrollView>
  );
}

function NoTest({ title, icon, colors }: { title: string; icon: any; colors: ReturnType<typeof useColors> }) {
  return (
    <View style={[nt.wrap, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <Feather name={icon} size={16} color={colors.mutedForeground} />
      <Text style={[nt.text, { color: colors.mutedForeground }]}>{title} — noch kein Test</Text>
    </View>
  );
}
const nt = StyleSheet.create({
  wrap: { flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 10, borderWidth: 1, borderStyle: 'dashed', padding: 14, marginBottom: 10 },
  text: { fontSize: 14, fontFamily: 'Inter_400Regular' },
});

const s = StyleSheet.create({
  root: { flex: 1 },
  hero: { alignItems: 'center', paddingBottom: 4 },
  avatarWrap: { width: 72, height: 72, borderRadius: 36, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  avatarText: { fontSize: 26, fontFamily: 'Inter_700Bold' },
  playerName: { fontSize: 22, fontFamily: 'Inter_700Bold', letterSpacing: -0.3 },
  playerMeta: { fontSize: 14, fontFamily: 'Inter_400Regular', marginTop: 4 },
  sectionTitle: { fontSize: 11, fontFamily: 'Inter_600SemiBold', letterSpacing: 1, marginBottom: 8 },
  actions: {},
  actionsRow: { flexDirection: 'row', gap: 10 },
  actionBtn: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 6, borderWidth: 1, borderRadius: 10, paddingVertical: 14 },
  actionLabel: { fontSize: 12, fontFamily: 'Inter_500Medium' },
  results: {},
  errText: { fontSize: 16, fontFamily: 'Inter_400Regular', marginTop: 12 },
  retryBtn: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 16, paddingVertical: 8, marginTop: 8 },
  retryText: { fontSize: 14, fontFamily: 'Inter_500Medium' },
});
