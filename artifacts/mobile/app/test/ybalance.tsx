import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useColors } from '@/hooks/useColors';
import { useMobileSubmitYbalance, getMobileGetPlayerQueryKey, getMobileGetPlayersQueryKey } from '@workspace/api-client-react';
import { useQueryClient } from '@tanstack/react-query';
import { KeyboardAwareScrollViewCompat } from '@/components/KeyboardAwareScrollViewCompat';

type Direction = 'ant' | 'pm' | 'pl';
type Side = 'r' | 'l';

const DIRECTIONS: Array<{ key: Direction; label: string; full: string }> = [
  { key: 'ant', label: 'ANT', full: 'Anterior' },
  { key: 'pm', label: 'PM', full: 'Posteromedial' },
  { key: 'pl', label: 'PL', full: 'Posterolateral' },
];

function ReachInput({
  label,
  value,
  onChange,
  colors,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  colors: ReturnType<typeof useColors>;
}) {
  return (
    <View style={ri.wrap}>
      <Text style={[ri.label, { color: colors.mutedForeground }]}>{label}</Text>
      <View style={[ri.inputRow, { backgroundColor: colors.secondary, borderColor: colors.border }]}>
        <TextInput
          style={[ri.input, { color: colors.foreground }]}
          value={value}
          onChangeText={onChange}
          placeholder="—"
          placeholderTextColor={colors.mutedForeground}
          keyboardType="decimal-pad"
          returnKeyType="next"
        />
        <Text style={[ri.unit, { color: colors.mutedForeground }]}>cm</Text>
      </View>
    </View>
  );
}
const ri = StyleSheet.create({
  wrap: { flex: 1, gap: 6 },
  label: { fontSize: 11, fontFamily: 'Inter_600SemiBold', letterSpacing: 0.5, textAlign: 'center' },
  inputRow: { flexDirection: 'row', alignItems: 'center', borderRadius: 8, borderWidth: 1 },
  input: { flex: 1, fontSize: 18, fontFamily: 'Inter_700Bold', paddingHorizontal: 10, paddingVertical: 10, textAlign: 'center' },
  unit: { paddingRight: 8, fontSize: 12, fontFamily: 'Inter_400Regular' },
});

function parseNum(s: string): number | null {
  const v = parseFloat(s.replace(',', '.'));
  return isNaN(v) || v <= 0 ? null : v;
}

function computeComposite(ant: number | null, pm: number | null, pl: number | null): number | null {
  if (!ant || !pm || !pl) return null;
  return Math.round(((ant + pm + pl) / 3) * 10) / 10;
}

function AsymmetryIndicator({ r, l, colors }: { r: number | null; l: number | null; colors: ReturnType<typeof useColors> }) {
  if (!r || !l) return null;
  const diff = Math.abs(r - l);
  const pct = Math.round((diff / Math.max(r, l)) * 100);
  const isAsym = diff > 4;
  const color = isAsym ? '#F59E0B' : colors.primary;
  return (
    <View style={[ai.wrap, { backgroundColor: color + '18' }]}>
      <Feather name={isAsym ? 'alert-triangle' : 'check'} size={14} color={color} />
      <Text style={[ai.text, { color }]}>
        {isAsym ? `Asymmetrie: ${pct}%` : 'Symmetrisch'}
      </Text>
    </View>
  );
}
const ai = StyleSheet.create({
  wrap: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  text: { fontSize: 13, fontFamily: 'Inter_500Medium' },
});

export default function YbalanceScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { playerId, playerName } = useLocalSearchParams<{ playerId: string; playerName: string }>();
  const id = parseInt(playerId ?? '0', 10);
  const queryClient = useQueryClient();

  const [fields, setFields] = useState<Record<string, string>>({
    ant_r: '', ant_l: '', pm_r: '', pm_l: '', pl_r: '', pl_l: '',
    leg_r: '', leg_l: '',
  });
  const [saved, setSaved] = useState<{ score: number | null; sub: number | null; msg: string } | null>(null);

  const { mutate, isPending } = useMobileSubmitYbalance({
    mutation: {
      onSuccess: (data) => {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setSaved({ score: data.score ?? null, sub: data.sub_score ?? null, msg: data.message });
        queryClient.invalidateQueries({ queryKey: getMobileGetPlayersQueryKey() });
        if (id) queryClient.invalidateQueries({ queryKey: getMobileGetPlayerQueryKey(id) });
      },
      onError: () => {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        Alert.alert('Fehler', 'Test konnte nicht gespeichert werden.');
      },
    },
  });

  const set = (key: string) => (v: string) => setFields((prev) => ({ ...prev, [key]: v }));

  const nums = {
    ant_r: parseNum(fields.ant_r), ant_l: parseNum(fields.ant_l),
    pm_r: parseNum(fields.pm_r), pm_l: parseNum(fields.pm_l),
    pl_r: parseNum(fields.pl_r), pl_l: parseNum(fields.pl_l),
    leg_r: parseNum(fields.leg_r), leg_l: parseNum(fields.leg_l),
  };

  const compR = computeComposite(nums.ant_r, nums.pm_r, nums.pl_r);
  const compL = computeComposite(nums.ant_l, nums.pm_l, nums.pl_l);
  const valid = nums.ant_r && nums.ant_l && nums.pm_r && nums.pm_l && nums.pl_r && nums.pl_l;

  const topPad = insets.top + (Platform.OS === 'web' ? 67 : 0);

  if (saved) {
    return (
      <View style={[s.root, { backgroundColor: colors.background, paddingTop: topPad + 60 }]}>
        <View style={s.successWrap}>
          <View style={[s.successIcon, { backgroundColor: colors.primary + '20' }]}>
            <Feather name="check-circle" size={40} color={colors.primary} />
          </View>
          <Text style={[s.successTitle, { color: colors.foreground }]}>Y-Balance gespeichert!</Text>
          <Text style={[s.successMsg, { color: colors.mutedForeground }]}>{saved.msg}</Text>
          {saved.score != null && (
            <View style={[s.scorePill, { backgroundColor: colors.primary + '18' }]}>
              <Text style={[s.scorePillVal, { color: colors.primary }]}>{saved.score}</Text>
              <Text style={[s.scorePillLabel, { color: colors.primary }]}>Athletik Score</Text>
            </View>
          )}
          <View style={s.successActions}>
            <Pressable
              style={[s.btn, { backgroundColor: colors.primary }]}
              onPress={() => { setSaved(null); setFields({ ant_r: '', ant_l: '', pm_r: '', pm_l: '', pl_r: '', pl_l: '', leg_r: '', leg_l: '' }); }}
            >
              <Text style={[s.btnText, { color: colors.primaryForeground }]}>Neuer Test</Text>
            </Pressable>
            <Pressable style={[s.btnOutline, { borderColor: colors.border }]} onPress={() => router.back()}>
              <Text style={[s.btnOutlineText, { color: colors.foreground }]}>Zurück</Text>
            </Pressable>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={[s.root, { backgroundColor: colors.background }]}>
      <KeyboardAwareScrollViewCompat
        contentContainerStyle={{ paddingTop: topPad + 60, paddingHorizontal: 16, paddingBottom: insets.bottom + 100 + (Platform.OS === 'web' ? 34 : 0), gap: 14 }}
        keyboardShouldPersistTaps="handled"
        bottomOffset={120}
        showsVerticalScrollIndicator={false}
      >
        <Text style={[s.playerLabel, { color: colors.mutedForeground }]}>{playerName}</Text>

        {/* Direction rows */}
        {DIRECTIONS.map(({ key, label, full }) => (
          <View key={key} style={[s.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
            <View style={s.cardHead}>
              <View style={[s.iconWrap, { backgroundColor: colors.primary + '18' }]}>
                <Text style={[s.dirLabel, { color: colors.primary }]}>{label}</Text>
              </View>
              <Text style={[s.cardTitle, { color: colors.foreground }]}>{full}</Text>
            </View>
            <View style={s.sideRow}>
              <ReachInput label="RECHTS" value={fields[`${key}_r`]!} onChange={set(`${key}_r`)} colors={colors} />
              <View style={[s.divider, { backgroundColor: colors.border }]} />
              <ReachInput label="LINKS" value={fields[`${key}_l`]!} onChange={set(`${key}_l`)} colors={colors} />
            </View>
          </View>
        ))}

        {/* Live composites */}
        {(compR != null || compL != null) && (
          <View style={[s.compCard, { backgroundColor: colors.secondary, borderColor: colors.border }]}>
            <Text style={[s.compTitle, { color: colors.foreground }]}>Composite Score (Ø)</Text>
            <View style={s.compRow}>
              {compR != null && (
                <View style={s.compItem}>
                  <Text style={[s.compVal, { color: colors.primary }]}>{compR}</Text>
                  <Text style={[s.compLabel, { color: colors.mutedForeground }]}>Rechts</Text>
                </View>
              )}
              {compL != null && (
                <View style={s.compItem}>
                  <Text style={[s.compVal, { color: colors.primary }]}>{compL}</Text>
                  <Text style={[s.compLabel, { color: colors.mutedForeground }]}>Links</Text>
                </View>
              )}
            </View>
            <AsymmetryIndicator r={compR} l={compL} colors={colors} />
          </View>
        )}

        {/* Optional leg length */}
        <View style={[s.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={s.cardHead}>
            <Feather name="maximize-2" size={16} color={colors.mutedForeground} />
            <Text style={[s.cardTitle, { color: colors.foreground }]}>Beinlänge (optional)</Text>
          </View>
          <View style={s.sideRow}>
            <ReachInput label="RECHTS" value={fields.leg_r!} onChange={set('leg_r')} colors={colors} />
            <View style={[s.divider, { backgroundColor: colors.border }]} />
            <ReachInput label="LINKS" value={fields.leg_l!} onChange={set('leg_l')} colors={colors} />
          </View>
          <Text style={[s.hintText, { color: colors.mutedForeground }]}>
            Mit Beinlänge wird der Composite-Score normalisiert
          </Text>
        </View>
      </KeyboardAwareScrollViewCompat>

      <View style={[s.footer, { paddingBottom: insets.bottom + 16 + (Platform.OS === 'web' ? 34 : 0), backgroundColor: colors.background, borderTopColor: colors.border }]}>
        <Pressable
          style={({ pressed }) => [s.saveBtn, { backgroundColor: colors.primary, opacity: isPending || !valid || !id ? 0.5 : pressed ? 0.85 : 1 }]}
          disabled={isPending || !valid || !id}
          onPress={() => {
            const today = new Date().toISOString().slice(0, 10);
            mutate({
              playerId: id,
              data: {
                datum: today,
                ant_r: nums.ant_r!, ant_l: nums.ant_l!,
                pm_r: nums.pm_r!, pm_l: nums.pm_l!,
                pl_r: nums.pl_r!, pl_l: nums.pl_l!,
                leg_length_r: nums.leg_r ?? undefined,
                leg_length_l: nums.leg_l ?? undefined,
              },
            });
          }}
        >
          {isPending ? <ActivityIndicator color={colors.primaryForeground} /> : <Text style={[s.saveBtnText, { color: colors.primaryForeground }]}>Speichern</Text>}
        </Pressable>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  playerLabel: { fontSize: 13, fontFamily: 'Inter_400Regular', marginBottom: -4 },
  card: { borderRadius: 12, borderWidth: 1, padding: 14, gap: 12 },
  cardHead: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  iconWrap: { width: 36, height: 36, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  dirLabel: { fontSize: 11, fontFamily: 'Inter_700Bold' },
  cardTitle: { fontSize: 14, fontFamily: 'Inter_600SemiBold', flex: 1 },
  sideRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  divider: { width: 1, height: 48, borderRadius: 1 },
  compCard: { borderRadius: 12, borderWidth: 1, padding: 14, gap: 10 },
  compTitle: { fontSize: 13, fontFamily: 'Inter_600SemiBold' },
  compRow: { flexDirection: 'row', gap: 16 },
  compItem: { alignItems: 'center', gap: 2 },
  compVal: { fontSize: 22, fontFamily: 'Inter_700Bold' },
  compLabel: { fontSize: 11, fontFamily: 'Inter_400Regular' },
  hintText: { fontSize: 11, fontFamily: 'Inter_400Regular' },
  footer: { paddingHorizontal: 16, paddingTop: 12, borderTopWidth: 1 },
  saveBtn: { borderRadius: 12, paddingVertical: 16, alignItems: 'center' },
  saveBtnText: { fontSize: 16, fontFamily: 'Inter_600SemiBold' },
  successWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32, gap: 16 },
  successIcon: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center' },
  successTitle: { fontSize: 22, fontFamily: 'Inter_700Bold' },
  successMsg: { fontSize: 14, fontFamily: 'Inter_400Regular', textAlign: 'center' },
  scorePill: { paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, alignItems: 'center' },
  scorePillVal: { fontSize: 28, fontFamily: 'Inter_700Bold' },
  scorePillLabel: { fontSize: 12, fontFamily: 'Inter_500Medium', marginTop: 2 },
  successActions: { width: '100%', gap: 10, marginTop: 8 },
  btn: { borderRadius: 12, paddingVertical: 14, alignItems: 'center' },
  btnText: { fontSize: 15, fontFamily: 'Inter_600SemiBold' },
  btnOutline: { borderRadius: 12, borderWidth: 1, paddingVertical: 14, alignItems: 'center' },
  btnOutlineText: { fontSize: 15, fontFamily: 'Inter_600SemiBold' },
});
