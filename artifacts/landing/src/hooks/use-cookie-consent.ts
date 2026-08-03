import { useState, useEffect } from 'react';

export function useCookieConsent() {
  const [consentGiven, setConsentGiven] = useState<boolean | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('cookie_consent');
    if (stored === 'true') {
      setConsentGiven(true);
    } else {
      setConsentGiven(false);
    }
  }, []);

  const acceptCookies = () => {
    localStorage.setItem('cookie_consent', 'true');
    setConsentGiven(true);
  };

  return { consentGiven, acceptCookies };
}
