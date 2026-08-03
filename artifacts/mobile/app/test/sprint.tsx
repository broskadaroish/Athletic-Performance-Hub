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
import { useMobileSubmitSprint, getMobileGetPlayerQueryKey, getMobileGetPlayersQueryKey } from '@workspace/api-client-react';
import { useQueryClient } from '@tanstack/react-query';
import { KeyboardAwareScrollViewCompat } from '@/components/KeyboardAwareScrollViewCompat';

function RatingBadge({ time, threshold }: { time: number | null; threshold: [number, number, number, number] }) {
  const colors = useColors();
  if (!time || time <= 0) return null;
  const [t1, t2, t3, t4] = threshold;
  const label = time <= t1 ? 'Hervorragend' : time <= t2 ? 'Gut' : time <= t3 ? 'Durchschnittlich' : time <= t4 ? 'Unterdurchschnittlich' : 'Schlecht';
  const color = time <= t1 ? colors.primary : time <= t2 ? '#10B981' : time <= t3 ? '#F59E0B' : colors.destructive;
  return (
    <Text style={[rb.tag, { color, backgroundColor: color + '18' }]}>{label}</Text>
  );
}
const rb = StyleSheet.create({ tag: { fontSize: 12, fontFamily: 'Inter_600SemiBold', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 } });

export default function SprintScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { playerId, playerName } = useLocalSearchParams<{ playerId: string; playerName: string }>();
  const id = parseInt(playerId ?? '0', 10);
  const queryClient = useQueryClient();

  const [t10, setT10] = useState('');
  const [t30, setT30] = useState('');
  const [saved, setSaved] = useState<{ score: number | null; msg: string } | null>(null);

  const { mutate, isPending } = useMobileSubmitSprint({
    mutation: {
      onSuccess: (data) => {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setSaved({ score: data.score ?? null, msg: data.message });
        queryClient.invalidateQueries({ queryKey: getMobileGetPlayersQueryKey() });
        if (id) queryClient.invalidateQueries({ queryKey: getMobileGetPlayerQueryKey(id) });
      },
      onError: () => {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        Alert.alert('Fehler', 'Test konnte nicht gespeichert werden.');
      },
    },
  });

  const topPad = insets.top + (Platform.OS === 'web' ? 67 : 0);
  const time10 = parseFloat(t10.replace(',', '.'));
  const time30 = parseFloat(t30.replace(',', '.'));
  const valid = !isNaN(time10) && time10 > 0;

  if (saved) {
    return (
      <View style={[s.root, { backgroundColor: colors.background, paddingTop: topPad + 60 }]}>
        <View style={s.successWrap}>
          <View style={[s.successIcon, { backgroundColor: colors.primary + '20' }]}>
            <Feather name="check-circle" size={40} color={colors.primary} />
          </View>
          <Text style={[s.successTitle, { color: colors.foreground }]}>Sprint gespeichert!</Text>
          <Text style={[s.successMsg, { color: colors.mutedForeground }]}>{saved.msg}</Text>
          {saved.score != null && (
            <View style={[s.scorePill, { backgroundColor: colors.primary + '18' }]}>
              <Text style={[s.scorePillVal, { color: colors.primary }]}>{saved.score}</Text>
              <Text style={[s.scorePillLabel, { color: colors.primary }]}>Athletik Score</Text>
            </View>
          )}
          <View style={s.successActions}>
            <Pressable style={[s.btn, { backgroundColor: colors.primary }]} onPress={() => { setSaved(null); setT10(''); setT30(''); }}>
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
        contentContainerStyle={{ paddingTop: topPad + 60, paddingHorizontal: 16, paddingBottom: insets.bottom + 100 + (Platform.OS === 'web' ? 34 : 0), gap: 16 }}
        keyboardShouldPersistTaps="handled"
        bottomOffset={120}
        showsVerticalScrollIndicator={false}
      >
        <Text style={[s.playerLabel, { color: colors.mutedForeground }]}>{playerName}</Text>

        {/* 10m */}
        <View style={[s.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={s.cardHead}>
            <View style={[s.iconWrap, { backgroundColor: colors.primary + '18' }]}>
              <Text style={[s.dist, { color: colors.primary }]}>10m</Text>
            </View>
            <View style={s.cardInfo}>
              <Text style={[s.cardTitle, { color: colors.foreground }]}>10-Meter-Sprint</Text>
              <Text style={[s.cardSub, { color: colors.mutedForeground }]}>Beschleunigung</Text>
            </View>
            <RatingBadge time={isNaN(time10) ? null : time10} threshold={[1.60, 1.72, 1.85, 2.00]} />
          </View>
          <View style={[s.inputWrap, { borderColor: colors.border, backgroundColor: colors.secondary }]}>
            <TextInput
              style={[s.input, { color: colors.foreground }]}
              value={t10}
              onChangeText={setT10}
              placeholder="1.72"
              placeholderTextColor={colors.mutedForeground}
              keyboardType="decimal-pad"
              returnKeyType="next"
            />
            <Text style={[s.unit, { color: colors.mutedForeground }]}>s</Text>
          </View>
        </View>

        {/* 30m */}
        <View style={[s.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <View style={s.cardHead}>
            <View style={[s.iconWrap, { backgroundColor: colors.primary + '18' }]}>
              <Text style={[s.dist, { color: colors.primary }]}>30m</Text>
            </View>
            <View style={s.cardInfo}>
              <Text style={[s.cardTitle, { color: colors.foreground }]}>30-Meter-Sprint</Text>
              <Text style={[s.cardSub, { color: colors.mutedForeground }]}>Maximalgeschwindigkeit (optional)</Text>
            </View>
            <RatingBadge time={isNaN(time30) || !t30 ? null : time30} threshold={[3.90, 4.10, 4.35, 4.65]} />
          </View>
          <View style={[s.inputWrap, { borderColor: colors.border, backgroundColor: colors.secondary }]}>
            <TextInput
              style={[s.input, { color: colors.foreground }]}
              value={t30}
              onChangeText={setT30}
              placeholder="4.10"
              placeholderTextColor={colors.mutedForeground}
              keyboardType="decimal-pad"
              returnKeyType="done"
            />
            <Text style={[s.unit, { color: colors.mutedForeground }]}>s</Text>
          </View>
        </View>

        {/* Norm hint */}
        <View style={[s.hint, { backgroundColor: colors.secondary }]}>
          <Feather name="info" size={14} color={colors.mutedForeground} />
          <Text style={[s.hintText, { color: colors.mutedForeground }]}>
            Normen: 10m — Hervorragend ≤ 1.60s · Gut ≤ 1.72s · Durchschnittlich ≤ 1.85s
          </Text>
        </View>
      </KeyboardAwareScrollViewCompat>

      <View style={[s.footer, { paddingBottom: insets.bottom + 16 + (Platform.OS === 'web' ? 34 : 0), backgroundColor: colors.background, borderTopColor: colors.border }]}>
        <Pressable
          style={({ pressed }) => [s.saveBtn, { backgroundColor: colors.primary, opacity: isPending || !valid || !id ? 0.5 : pressed ? 0.85 : 1 }]}
          disabled={isPending || !valid || !id}
          onPress={() => {
            const today = new Date().toISOString().slice(0, 10);
            mutate({ playerId: id, data: { datum: today, best_10m: time10, best_30m: isNaN(time30) || !t30 ? time10 : time30 } });
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
  card: { borderRadius: 12, borderWidth: 1, padding: 16, gap: 12 },
  cardHead: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconWrap: { width: 44, height: 44, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  dist: { fontSize: 13, fontFamily: 'Inter_700Bold' },
  cardInfo: { flex: 1 },
  cardTitle: { fontSize: 15, fontFamily: 'Inter_600SemiBold' },
  cardSub: { fontSize: 12, fontFamily: 'Inter_400Regular', marginTop: 2 },
  inputWrap: { flexDirection: 'row', alignItems: 'center', borderRadius: 10, borderWidth: 1, overflow: 'hidden' },
  input: { flex: 1, fontSize: 22, fontFamily: 'Inter_700Bold', paddingHorizontal: 16, paddingVertical: 12 },
  unit: { paddingHorizontal: 14, fontSize: 16, fontFamily: 'Inter_400Regular' },
  hint: { flexDirection: 'row', gap: 8, padding: 12, borderRadius: 10, alignItems: 'flex-start' },
  hintText: { flex: 1, fontSize: 12, fontFamily: 'Inter_400Regular', lineHeight: 18 },
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
