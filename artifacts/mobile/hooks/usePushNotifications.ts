/**
 * Registers the device for Expo push notifications and sends the token to the API.
 * Safe to call on web — gracefully returns null there.
 *
 * EAS Project ID: required by getExpoPushTokenAsync in Expo SDK 50+.
 * Set it via app.json → extra.eas.projectId (populated by `eas init`).
 * Without it the call still succeeds in Expo Go (dev client injects it);
 * on a standalone build, configure it before submitting to app stores.
 *
 * Expo Go + Android (SDK 53+): Remote push notifications were removed from
 * Expo Go. We detect Expo Go via Constants.appOwnership === 'expo' and skip
 * all notification setup on that platform/runtime combination so the app
 * does not crash. Push will still work in real Development Builds and
 * Production Builds where expo-notifications is fully supported.
 */
import { useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';

/**
 * True when running inside Expo Go (appOwnership === 'expo').
 * In this environment, Android remote push notifications are not available
 * since SDK 53. iOS Expo Go still supports local notifications but not
 * remote push, so we skip registration universally in Expo Go.
 */
const IS_EXPO_GO = Constants.appOwnership === 'expo';

// Register the notification handler only in real builds (Development Build /
// Production). In Expo Go this import-time call throws on Android SDK 53+.
if (!IS_EXPO_GO) {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
}

export async function registerForPushNotificationsAsync(): Promise<string | null> {
  // Push notifications are not supported on web
  if (Platform.OS === 'web') return null;

  // Skip in Expo Go — remote push not available (Android SDK 53+) and
  // registration would throw or silently fail. Real builds handle this.
  if (IS_EXPO_GO) return null;

  // PermissionResponse re-exported through expo/expo-modules-core has `granted`
  // but the TS definition via expo-notifications may not surface it — cast to access.
  const existingPerms = await Notifications.getPermissionsAsync() as unknown as { granted: boolean };
  let granted = existingPerms.granted;

  if (!granted) {
    const result = await Notifications.requestPermissionsAsync() as unknown as { granted: boolean };
    granted = result.granted;
  }

  if (!granted) return null;

  try {
    // projectId is required in Expo SDK 50+ for standalone builds.
    // In Expo Go / dev client it is injected automatically; in production
    // it must be set via app.json → extra.eas.projectId (run `eas init`).
    // projectId lives at expoConfig.extra.eas.projectId (populated by `eas init`).
    // Expo Go and dev clients inject it automatically at runtime.
    // For standalone builds, ensure app.json has extra.eas.projectId set.
    const extra = Constants.expoConfig?.extra as Record<string, unknown> | undefined;
    const easExtra = extra?.['eas'] as Record<string, unknown> | undefined;
    const projectId = easExtra?.['projectId'] as string | undefined;

    const tokenData = await Notifications.getExpoPushTokenAsync(
      projectId ? { projectId } : undefined,
    );
    return tokenData.data;
  } catch (err) {
    // Silently skip — push token registration is non-critical.
    // Common causes: no EAS project configured, simulator, permissions denied.
    console.warn('[PushNotifications] Token registration skipped:', err);
    return null;
  }
}

function getBaseUrl(): string {
  const domain = process.env['EXPO_PUBLIC_DOMAIN'];
  if (domain) return `https://${domain}`;
  return '';
}

/**
 * Hook: registers for push notifications after login and sends the token to the server.
 * Call with `token` from AuthContext (null = not logged in).
 */
export function usePushNotificationRegistration(authToken: string | null) {
  const registeredRef = useRef(false);

  useEffect(() => {
    if (!authToken || registeredRef.current) return;

    (async () => {
      const pushToken = await registerForPushNotificationsAsync();
      if (!pushToken) return;

      try {
        const base = getBaseUrl();
        await fetch(`${base}/api/mobile/push-token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({ token: pushToken }),
        });
        registeredRef.current = true;
      } catch {
        // Non-critical — silently ignore
      }
    })();
  }, [authToken]);

  // Reset registration flag when logged out
  useEffect(() => {
    if (!authToken) {
      registeredRef.current = false;
    }
  }, [authToken]);
}
