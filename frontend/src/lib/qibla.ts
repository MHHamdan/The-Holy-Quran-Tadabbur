/**
 * Qibla bearing and live device heading.
 *
 * The bearing is the initial great-circle course from the user's position to
 * the Kaaba, computed locally (no network, works offline).
 */
import { useCallback, useEffect, useRef, useState } from 'react';

/** The Kaaba, Makkah (WGS84). */
export const KAABA = { lat: 21.422487, lng: 39.826206 };

const rad = (d: number) => (d * Math.PI) / 180;
const deg = (r: number) => (r * 180) / Math.PI;

/** Degrees clockwise from true north, 0–360. */
export function qiblaBearing(lat: number, lng: number): number {
  const φ1 = rad(lat);
  const φ2 = rad(KAABA.lat);
  const Δλ = rad(KAABA.lng - lng);
  const y = Math.sin(Δλ);
  const x = Math.cos(φ1) * Math.tan(φ2) - Math.sin(φ1) * Math.cos(Δλ);
  return (deg(Math.atan2(y, x)) + 360) % 360;
}

/** Signed smallest difference a - b in degrees, in (-180, 180]. */
export function angleDiff(a: number, b: number): number {
  const d = ((a - b) % 360 + 540) % 360 - 180;
  return d === -180 ? 180 : d;
}

export type HeadingStatus = 'idle' | 'needs-permission' | 'active' | 'unsupported' | 'denied';

interface IOSOrientationEvent extends DeviceOrientationEvent {
  webkitCompassHeading?: number;
}
type PermissionRequester = { requestPermission?: () => Promise<'granted' | 'denied'> };

/**
 * Compass heading (degrees clockwise from north) from device orientation.
 * iOS needs an explicit permission request from a user gesture: call
 * `start()` from a button. Smoothed so the needle does not jitter.
 */
export function useDeviceHeading() {
  const [heading, setHeading] = useState<number | null>(null);
  const [status, setStatus] = useState<HeadingStatus>(() => {
    if (typeof window === 'undefined' || !('DeviceOrientationEvent' in window)) return 'unsupported';
    const needsPermission = typeof (DeviceOrientationEvent as unknown as PermissionRequester).requestPermission === 'function';
    return needsPermission ? 'needs-permission' : 'idle';
  });
  const smoothed = useRef<number | null>(null);
  const cleanup = useRef<(() => void) | null>(null);

  const listen = useCallback(() => {
    const onEvent = (e: Event) => {
      const ev = e as IOSOrientationEvent;
      let h: number | null = null;
      if (typeof ev.webkitCompassHeading === 'number') {
        h = ev.webkitCompassHeading; // iOS: already clockwise from north
      } else if (ev.absolute && ev.alpha !== null) {
        const screenAngle = window.screen?.orientation?.angle ?? 0;
        h = (360 - ev.alpha + screenAngle) % 360;
      }
      if (h === null) return;
      const prev = smoothed.current;
      const next = prev === null ? h : (prev + angleDiff(h, prev) * 0.25 + 360) % 360;
      smoothed.current = next;
      setHeading(next);
      setStatus('active');
    };
    // Android/Chrome emit absolute (north-referenced) readings on this event.
    const eventName = 'ondeviceorientationabsolute' in window ? 'deviceorientationabsolute' : 'deviceorientation';
    window.addEventListener(eventName, onEvent);
    cleanup.current = () => window.removeEventListener(eventName, onEvent);
  }, []);

  const start = useCallback(async () => {
    if (status === 'unsupported' || status === 'active') return;
    const requester = DeviceOrientationEvent as unknown as PermissionRequester;
    if (typeof requester.requestPermission === 'function') {
      try {
        if ((await requester.requestPermission()) !== 'granted') {
          setStatus('denied');
          return;
        }
      } catch {
        setStatus('denied');
        return;
      }
    }
    listen();
  }, [listen, status]);

  // No permission needed (Android, desktop): start right away.
  useEffect(() => {
    if (status === 'idle') listen();
  }, [status, listen]);

  useEffect(() => () => cleanup.current?.(), []);

  return { heading, status, start };
}
