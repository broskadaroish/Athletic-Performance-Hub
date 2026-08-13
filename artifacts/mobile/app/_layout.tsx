import React, { useEffect, useState } from 'react';
import { Platform } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { KeyboardProvider } from 'react-native-keyboard-controller';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import {
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
  Inter_700Bold,
  useFonts,
} from '@expo-google-fonts/inter';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { setBaseUrl } from '@workspace/api-client-react';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { OfflineQueueProvider } from '@/contexts/OfflineQueueContext';
import { usePushNotificationRegistration } from '@/hooks/usePushNotifications';

// Set base URL before any component renders (Expo bundles need absolute URLs)
if (process.env.EXPO_PUBLIC_DOMAIN) {
  setBaseUrl(`https://${process.env.EXPO_PUBLIC_DOMAIN}`);
}

// Prevent the splash screen from auto-hiding before asset loading is complete.
SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

/** Inner component — must live inside AuthProvider to access useAuth */
function PushRegistrar() {
  const { token } = useAuth();
  usePushNotificationRegistration(token);
  return null;
}

function RootLayoutNav() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="login" options={{ headerShown: false }} />
      <Stack.Screen
        name="player/[id]"
        options={{
          headerShown: true,
          headerTitle: '',
          headerTransparent: true,
          headerBackTitle: 'Zurück',
        }}
      />
      <Stack.Screen
        name="test/fms"
        options={{
          headerShown: true,
          headerTitle: 'FMS Test',
          headerBackTitle: 'Zurück',
        }}
      />
      <Stack.Screen
        name="test/sprint"
        options={{
          headerShown: true,
          headerTitle: 'Sprint Test',
          headerBackTitle: 'Zurück',
        }}
      />
      <Stack.Screen
        name="test/ybalance"
        options={{
          headerShown: true,
          headerTitle: 'Y-Balance Test',
          headerBackTitle: 'Zurück',
        }}
      />
    </Stack>
  );
}

// Android Expo Go: font loading can hang without triggering fontError,
// keeping the splash screen visible forever.  This timeout forces the
// splash to hide after 4 s so the login screen always appears.
const ANDROID_SPLASH_TIMEOUT_MS = 4_000;

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
  });

  // Safety: on Android, hide the splash screen after a fixed deadline even
  // if useFonts() never resolves.  On other platforms the normal effect below
  // handles it, so this no-ops there.
  const [splashForceHidden, setSplashForceHidden] = useState(false);
  useEffect(() => {
    if (Platform.OS !== 'android') return;
    const timer = setTimeout(() => {
      SplashScreen.hideAsync().catch(() => {});
      setSplashForceHidden(true);
    }, ANDROID_SPLASH_TIMEOUT_MS);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync().catch(() => {});
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError && !splashForceHidden) return null;

  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <OfflineQueueProvider>
              <PushRegistrar />
              <GestureHandlerRootView style={{ flex: 1 }}>
                <KeyboardProvider>
                  <RootLayoutNav />
                </KeyboardProvider>
              </GestureHandlerRootView>
            </OfflineQueueProvider>
          </AuthProvider>
        </QueryClientProvider>
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}
