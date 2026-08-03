import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
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
import { useMobileSubmitFms } from '@workspace/api-client-react';
import { useQueryClient } from '@tanstack/react-query';
import { getMobileGetPlayerQueryKey, getMobileGetPlayersQueryKey } from '@workspace/api-client-react';

type FmsValues = {
  deep_squat: number;
  hurdle_l: number; hurdle_r: number;
  inline_l: number; inline_r: number;
  shoulder_l: number; shoulder_r: number;
  aslr_l: number; aslr_r: number;
  trunk: number;
  rotary_l: number; rotary_r: number;
};

const PATTERNS: Array<{ key: string; label: string; bilateral: boolean; maxScore: number }> = [
  { key: 'deep_squat', label: 'Deep Squat', bilateral: false, maxScore: 3 },
  { key: 'hurdle', label: 'Hurdle Step', bilateral: true, maxScore: 3 },
  { key: 'inline', label: 'Inline Lunge', bilateral: true, maxScore: 3 },
  { key: 'shoulder', label: 'Shoulder Mobility', bilateral: true, maxScore: 3 },
  { key: 'aslr', label: 'Active SLR', bilateral: true, maxScore: 3 },
  { key: 'trunk', label: 'Trunk Stability Push-Up', bilateral: false, maxScore: 3 },
  { key: 'rotary', label: 'Rotary Stability', bilateral: true, maxScore: 3 },
];

function ScoreButton({ value, target, onPress, colors }: {
  value: number; target: number;
  onPress: () => void;
  colors: ReturnType<typeof useColors>;
}) {
  const active = value === target;
  return (
    <Pressable
      style={[sb.btn, {
        backgroundColor: active ? colors.primary : colors.secondary,
        borderColor: active ? colors.primary : colors.border,
      }]}
      onPress={onPress}
    >
      <Text style={[sb.text, { color: active ? colors.primaryForeground : colors.mutedForeground }]}>{target}</Text>
    </Pressable>
  );
}
const sb = StyleSheet.create({
  btn: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', borderWidth: 1 },
  text: { fontSize: 16, fontFamily: 'Inter_600SemiBold' },
});

function computeScore(v: FmsValues): number {
  return v.deep_squat +
    Math.min(v.hurdle_l, v.hurdle_r) +
    Math.min(v.inline_l, v.inline_r) +
    Math.min(v.shoulder_l, v.shoulder_r) +
    Math.min(v.aslr_l, v.aslr_r) +
    v.trunk +
    Math.min(v.rotary_l, v.rotary_r);
}

export default function FmsScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { playerId, playerName } = useLocalSearchParams<{ playerId: string; playerName: string }>();
  const id = parseInt(playerId ?? '0', 10);
  const queryClient = useQueryClient();

  const [values, setValues] = useState<FmsValues>({
    deep_squat: 0, hurdle_l: 0, hurdle_r: 0, inline_l: 0, inline_r: 0,
    shoulder_l: 0, shoulder_r: 0, aslr_l: 0, aslr_r: 0, trunk: 0, rotary_l: 0, rotary_r: 0,
  });
  const [saved, setSaved] = useState<{ score: number; athletikScore: number | null } | null>(null);

  const { mutate, isPending } = useMobileSubmitFms({
    mutation: {
      onSuccess: (data) => {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setSaved({ score: data.sub_score ?? 0, athletikScore: data.score ?? null });
        queryClient.invalidateQueries({ queryKey: getMobileGetPlayersQueryKey() });
        if (id) queryClient.invalidateQueries({ queryKey: getMobileGetPlayerQueryKey(id) });
      },
      onError: () => {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        Alert.alert('Fehler', 'Test konnte nicht gespeichert werden.');
      },
    },
  });

  const set = (key: string, val: number) => {
    setValues((prev) => ({ ...prev, [key]: val }));
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const totalScore = computeScore(values);
  const topPad = insets.top + (Platform.OS === 'web' ? 67 : 0);

  if (saved) {
    const scoreColor = saved.score >= 14 ? colors.primary : saved.score >= 10 ? '#F59E0B' : colors.destructive;
    return (
      <View style={[s.root, { backgroundColor: colors.background, paddingTop: topPad + 60 }]}>
        <View style={s.successWrap}>
          <View style={[s.successIcon, { backgroundColor: colors.primary + '20' }]}>
            <Feather name="check-circle" size={40} color={colors.primary} />
          </View>
          <Text style={[s.successTitle, { color: colors.foreground }]}>FMS gespeichert!</Text>
          <View style={s.successScores}>
            <View style={[s.scorePill, { backgroundColor: scoreColor + '18' }]}>
              <Text style={[s.scorePillVal, { color: scoreColor }]}>{saved.score}</Text>
              <Text style={[s.scorePillLabel, { color: scoreColor }]}>/ 21</Text>
            </View>
            {saved.athletikScore != null && (
              <View style={[s.scorePill, { backgroundColor: colors.primary + '18' }]}>
                <Text style={[s.scorePillVal, { color: colors.primary }]}>{saved.athletikScore}</Text>
                <Text style={[s.scorePillLabel, { color: colors.primary }]}>Athletik</Text>
              </View>
            )}
          </View>
          <View style={s.successActions}>
            <Pressable
              style={[s.btn, { backgroundColor: colors.primary }]}
              onPress={() => {
                setSaved(null);
                setValues({ deep_squat: 0, hurdle_l: 0, hurdle_r: 0, inline_l: 0, inline_r: 0, shoulder_l: 0, shoulder_r: 0, aslr_l: 0, aslr_r: 0, trunk: 0, rotary_l: 0, rotary_r: 0 });
              }}
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
      {/* Score header */}
      <View style={[s.scoreHeader, { paddingTop: topPad + 60, backgroundColor: colors.background }]}>
        <Text style={[s.playerLabel, { color: colors.mutedForeground }]}>{playerName}</Text>
        <View style={s.scoreRow}>
          <Text style={[s.totalScore, { color: totalScore >= 14 ? colors.primary : totalScore >= 10 ? '#F59E0B' : colors.destructive }]}>
            {totalScore}
          </Text>
          <Text style={[s.totalMax, { color: colors.mutedForeground }]}>/21</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100 + (Platform.OS === 'web' ? 34 : 0), gap: 8 }}
        showsVerticalScrollIndicator={false}
      >
        {PATTERNS.map((p) => (
          <View key={p.key} style={[s.patternCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
            <Text style={[s.patternName, { color: colors.foreground }]}>{p.label}</Text>
            {p.bilateral ? (
              <View style={s.bilateral}>
                <View style={s.side}>
                  <Text style={[s.sideLabel, { color: colors.mutedForeground }]}>Links</Text>
                  <View style={s.btnRow}>
                    {[0, 1, 2, 3].map((v) => (
                      <ScoreButton key={v} value={values[`${p.key}_l` as keyof FmsValues]} target={v} onPress={() => set(`${p.key}_l`, v)} colors={colors} />
                    ))}
                  </View>
                </View>
                <View style={s.side}>
                  <Text style={[s.sideLabel, { color: colors.mutedForeground }]}>Rechts</Text>
                  <View style={s.btnRow}>
                    {[0, 1, 2, 3].map((v) => (
                      <ScoreButton key={v} value={values[`${p.key}_r` as keyof FmsValues]} target={v} onPress={() => set(`${p.key}_r`, v)} colors={colors} />
                    ))}
                  </View>
                </View>
              </View>
            ) : (
              <View style={s.btnRow}>
                {[0, 1, 2, 3].map((v) => (
                  <ScoreButton key={v} value={values[p.key as keyof FmsValues]} target={v} onPress={() => set(p.key, v)} colors={colors} />
                ))}
              </View>
            )}
          </View>
        ))}
      </ScrollView>

      {/* Save button */}
      <View style={[s.footer, { paddingBottom: insets.bottom + 16 + (Platform.OS === 'web' ? 34 : 0), backgroundColor: colors.background, borderTopColor: colors.border }]}>
        <Pressable
          style={({ pressed }) => [s.saveBtn, { backgroundColor: colors.primary, opacity: isPending || !id ? 0.6 : pressed ? 0.85 : 1 }]}
          disabled={isPending || !id}
          onPress={() => {
            const today = new Date().toISOString().slice(0, 10);
            mutate({ playerId: id, data: { datum: today, ...values } });
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
  scoreHeader: { paddingHorizontal: 16, paddingBottom: 12, alignItems: 'center' },
  playerLabel: { fontSize: 13, fontFamily: 'Inter_400Regular', marginBottom: 4 },
  scoreRow: { flexDirection: 'row', alignItems: 'baseline', gap: 4 },
  totalScore: { fontSize: 56, fontFamily: 'Inter_700Bold', letterSpacing: -2 },
  totalMax: { fontSize: 20, fontFamily: 'Inter_400Regular' },
  patternCard: { borderRadius: 12, borderWidth: 1, padding: 14, gap: 10 },
  patternName: { fontSize: 14, fontFamily: 'Inter_600SemiBold' },
  bilateral: { gap: 8 },
  side: { gap: 6 },
  sideLabel: { fontSize: 11, fontFamily: 'Inter_500Medium', letterSpacing: 0.5 },
  btnRow: { flexDirection: 'row', gap: 8 },
  footer: { paddingHorizontal: 16, paddingTop: 12, borderTopWidth: 1 },
  saveBtn: { borderRadius: 12, paddingVertical: 16, alignItems: 'center' },
  saveBtnText: { fontSize: 16, fontFamily: 'Inter_600SemiBold' },
  successWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32, gap: 16 },
  successIcon: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center' },
  successTitle: { fontSize: 22, fontFamily: 'Inter_700Bold' },
  successScores: { flexDirection: 'row', gap: 12 },
  scorePill: { paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, alignItems: 'center' },
  scorePillVal: { fontSize: 28, fontFamily: 'Inter_700Bold' },
  scorePillLabel: { fontSize: 12, fontFamily: 'Inter_500Medium', marginTop: 2 },
  successActions: { width: '100%', gap: 10, marginTop: 8 },
  btn: { borderRadius: 12, paddingVertical: 14, alignItems: 'center' },
  btnText: { fontSize: 15, fontFamily: 'Inter_600SemiBold' },
  btnOutline: { borderRadius: 12, borderWidth: 1, paddingVertical: 14, alignItems: 'center' },
  btnOutlineText: { fontSize: 15, fontFamily: 'Inter_600SemiBold' },
});
