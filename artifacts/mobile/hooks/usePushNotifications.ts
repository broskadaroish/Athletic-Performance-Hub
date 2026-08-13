/**
 * Registers the device for Expo push notifications and sends the token to the API.
 * Safe to call on web — gracefully returns null there.
 *
 * ### Expo Go + Android (SDK 53+)
 * Remote push notifications were removed from Expo Go.  Even *importing*
 * expo-notifications throws a fatal error on Android Expo Go SDK 53+.
 * We prevent the module from loading in that environment by using a
 * conditional require() instead of a static import.  Metro's module system is
 * lazy for require() — the factory function only runs when require() is called,
 * so skipping the call in Expo Go means the module is never initialized.
 *
 * Push notifications continue to work normally in real Development Builds and
 * Production Builds where expo-notifications is fully supported.
 */
import { useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
// Type-only import — erased by TypeScript, generates NO runtime require().
// Gives us full type-safety for the Notifications API without loading the module.
import type * as NotificationsType from 'expo-notifications';

/**
 * True when the app is running inside Expo Go (appOwnership === 'expo').
 * In this environment, Android SDK 53+ throws on import of expo-notifications.
 */
const IS_EXPO_GO = Constants.appOwnership === 'expo';

/**
 * Lazily loads expo-notifications via require() so Metro's module factory
 * only executes in real builds.  Returns null in Expo Go or if the module
 * fails to load for any reason.
 */
function loadNotificationsModule(): typeof NotificationsType | null {
  if (IS_EXPO_GO) return null;
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    return require('expo-notifications') as typeof NotificationsType;
  } catch {
    return null;
  }
}

const Notifications = loadNotificationsModule();

// Register the global notification handler — only in real builds.
// Calling this in Expo Go is both unnecessary and fatal on Android SDK 53+.
if (Notifications) {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export async function registerForPushNotificationsAsync(): Promise<string | null> {
  // Push notifications are not supported on web
  if (Platform.OS === 'web') return null;

  // Skip in Expo Go — remote push not available and module not loaded.
  if (IS_EXPO_GO || !Notifications) return null;

  const existingPerms =
    (await Notifications.getPermissionsAsync()) as unknown as { granted: boolean };
  let granted = existingPerms.granted;

  if (!granted) {
    const result =
      (await Notifications.requestPermissionsAsync()) as unknown as { granted: boolean };
    granted = result.granted;
  }

  if (!granted) return null;

  try {
    // projectId is required in Expo SDK 50+ for standalone builds.
    // Expo Go / dev clients inject it automatically; for production builds
    // ensure app.json has extra.eas.projectId set (run `eas init`).
    const extra = Constants.expoConfig?.extra as Record<string, unknown> | undefined;
    const easExtra = extra?.['eas'] as Record<string, unknown> | undefined;
    const projectId = easExtra?.['projectId'] as string | undefined;

    const tokenData = await Notifications.getExpoPushTokenAsync(
      projectId ? { projectId } : undefined,
    );
    return tokenData.data;
  } catch (err) {
    // Silently skip — push token registration is non-critical.
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
 * Hook: registers for push notifications after login and sends the token to
 * the server.  Call with `token` from AuthContext (null = not logged in).
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
