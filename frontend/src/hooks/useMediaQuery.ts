import { useEffect, useState } from 'react';

function matches(query: string): boolean {
  try {
    return typeof window !== 'undefined' && window.matchMedia(query).matches;
  } catch {
    return false;
  }
}

/** True while the CSS media query matches; updates when it changes. */
export function useMediaQuery(query: string): boolean {
  const [state, setState] = useState(() => matches(query));
  useEffect(() => {
    let mql: MediaQueryList;
    try {
      mql = window.matchMedia(query);
    } catch {
      return;
    }
    const onChange = () => setState(mql.matches);
    onChange();
    mql.addEventListener?.('change', onChange);
    return () => mql.removeEventListener?.('change', onChange);
  }, [query]);
  return state;
}
