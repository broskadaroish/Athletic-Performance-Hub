import React, { useState } from 'react';
import {
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Redirect } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { useColors } from '@/hooks/useColors';
import { useAuth } from '@/contexts/AuthContext';
import { mobileLogin } from '@workspace/api-client-react';
import type { AuthUser } from '@/contexts/AuthContext';

export default function LoginScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { token, login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (token) return <Redirect href="/(tabs)" />;

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      setError('Bitte E-Mail und Passwort eingeben');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await mobileLogin({ email: email.trim(), password });
      await login(res.token, res.user as AuthUser);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (err: any) {
      const msg = err?.response?.data?.error ?? err?.message ?? 'Login fehlgeschlagen';
      setError(msg);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  };

  const s = styles(colors, insets);

  return (
    <View style={s.root}>
      <KeyboardAvoidingView
        style={s.kav}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={s.top}>
          <Image
            source={require('../assets/images/icon.png')}
            style={s.icon}
            resizeMode="contain"
          />
          <Text style={s.appName}>Athletik</Text>
          <Text style={s.subtitle}>Trainer-App</Text>
        </View>

        <View style={s.form}>
          <View style={s.inputWrap}>
            <Text style={s.label}>E-Mail</Text>
            <TextInput
              style={s.input}
              value={email}
              onChangeText={setEmail}
              placeholder="trainer@verein.de"
              placeholderTextColor={colors.mutedForeground}
              autoCapitalize="none"
              keyboardType="email-address"
              autoComplete="email"
              returnKeyType="next"
            />
          </View>

          <View style={s.inputWrap}>
            <Text style={s.label}>Passwort</Text>
            <TextInput
              style={s.input}
              value={password}
              onChangeText={setPassword}
              placeholder="••••••••"
              placeholderTextColor={colors.mutedForeground}
              secureTextEntry
              autoComplete="current-password"
              returnKeyType="done"
              onSubmitEditing={handleLogin}
            />
          </View>

          {error && <Text style={s.error}>{error}</Text>}

          <Pressable
            style={({ pressed }) => [s.btn, pressed && s.btnPressed, loading && s.btnDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color={colors.primaryForeground} />
            ) : (
              <Text style={s.btnText}>Anmelden</Text>
            )}
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = (c: ReturnType<typeof useColors>, insets: ReturnType<typeof useSafeAreaInsets>) =>
  StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: c.background,
    },
    kav: {
      flex: 1,
      justifyContent: 'center',
      paddingHorizontal: 28,
      paddingTop: insets.top + (Platform.OS === 'web' ? 67 : 0),
      paddingBottom: insets.bottom + (Platform.OS === 'web' ? 34 : 0),
    },
    top: {
      alignItems: 'center',
      marginBottom: 48,
    },
    icon: {
      width: 72,
      height: 72,
      borderRadius: 18,
      marginBottom: 16,
    },
    appName: {
      fontSize: 32,
      fontFamily: 'Inter_700Bold',
      color: c.foreground,
      letterSpacing: -0.5,
    },
    subtitle: {
      fontSize: 15,
      fontFamily: 'Inter_400Regular',
      color: c.mutedForeground,
      marginTop: 4,
    },
    form: {
      gap: 16,
    },
    inputWrap: {
      gap: 6,
    },
    label: {
      fontSize: 13,
      fontFamily: 'Inter_500Medium',
      color: c.mutedForeground,
      letterSpacing: 0.3,
    },
    input: {
      backgroundColor: c.card,
      borderWidth: 1,
      borderColor: c.border,
      borderRadius: c.radius,
      paddingHorizontal: 16,
      paddingVertical: 14,
      fontSize: 16,
      fontFamily: 'Inter_400Regular',
      color: c.foreground,
    },
    error: {
      fontSize: 13,
      fontFamily: 'Inter_400Regular',
      color: c.destructive,
      textAlign: 'center',
    },
    btn: {
      backgroundColor: c.primary,
      borderRadius: c.radius,
      paddingVertical: 16,
      alignItems: 'center',
      marginTop: 8,
    },
    btnPressed: { opacity: 0.85 },
    btnDisabled: { opacity: 0.6 },
    btnText: {
      fontSize: 16,
      fontFamily: 'Inter_600SemiBold',
      color: c.primaryForeground,
    },
  });
