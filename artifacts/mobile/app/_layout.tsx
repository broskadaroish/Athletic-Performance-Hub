import React, { useEffect } from 'react';
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
import { useColorScheme } from 'react-native';
import { SystemUI } from 'expo-system-ui';
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

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) return null;

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
