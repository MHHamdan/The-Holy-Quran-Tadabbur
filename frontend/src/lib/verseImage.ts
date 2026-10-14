/**
 * Share a verse as an image (1080×1350 PNG, the 4:5 social format).
 *
 * The verse text comes from the API like everywhere else; the image adds the
 * reference, an optional translation with its edition, and the Tanzil
 * attribution its licence requires. Shared through the native share sheet in
 * the apps, Web Share with files where supported, else downloaded.
 */
import { isNativeApp } from './native';

export interface VerseImageContent {
  arabic: string;
  reference: string;          // e.g. "Al-Baqara 2:255" / "البقرة ٢٥٥"
  translation?: string;
  translationSource?: string; // edition title, shown under the translation
  arabicFont: string;         // CSS font family available in the page
}

const W = 1080;
const H = 1350;
const PAD = 90;

function wrap(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const lines: string[] = [];
  let line = '';
  for (const word of text.split(/\s+/).filter(Boolean)) {
    const candidate = line ? `${line} ${word}` : word;
    if (ctx.measureText(candidate).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
  }
  if (line) lines.push(line);
  return lines;
}

/** Largest font size (from start down) at which the text fits in maxLines. */
function fit(ctx: CanvasRenderingContext2D, text: string, font: (size: number) => string,
  start: number, min: number, maxWidth: number, maxHeight: number, lineHeight: number) {
  for (let size = start; size >= min; size -= 2) {
    ctx.font = font(size);
    const lines = wrap(ctx, text, maxWidth);
    if (lines.length * size * lineHeight <= maxHeight) return { size, lines };
  }
  ctx.font = font(min);
  return { size: min, lines: wrap(ctx, text, maxWidth) };
}

export async function renderVerseImage(c: VerseImageContent): Promise<Blob> {
  const arabicFont = (size: number) => `${size}px "${c.arabicFont}", "Noto Naskh Arabic", serif`;
  const latinFont = (size: number, weight = 400) => `${weight} ${size}px Inter, system-ui, sans-serif`;
  try {
    await Promise.all([document.fonts.load(arabicFont(64), c.arabic), document.fonts.load(latinFont(30))]);
  } catch { /* fall back to whatever is loaded */ }

  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('canvas unavailable');

  // Background and frame
  const bg = ctx.createLinearGradient(0, 0, W, H);
  bg.addColorStop(0, '#0c4a6e');
  bg.addColorStop(1, '#075985');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(253, 230, 138, 0.55)';
  ctx.lineWidth = 3;
  ctx.strokeRect(40, 40, W - 80, H - 80);

  const textWidth = W - PAD * 2;
  const hasTranslation = !!c.translation;
  const arabicBox = hasTranslation ? 620 : 900;

  // Arabic verse (right to left, centred)
  ctx.direction = 'rtl';
  ctx.textAlign = 'center';
  ctx.fillStyle = '#ffffff';
  const ar = fit(ctx, c.arabic, arabicFont, 64, 30, textWidth, arabicBox, 1.9);
  ctx.font = arabicFont(ar.size);
  const arHeight = ar.lines.length * ar.size * 1.9;
  let y = 150 + (arabicBox - arHeight) / 2 + ar.size;
  for (const line of ar.lines) {
    ctx.fillText(line, W / 2, y);
    y += ar.size * 1.9;
  }

  // Translation of the meanings
  if (hasTranslation) {
    ctx.direction = 'ltr';
    ctx.fillStyle = '#e0f2fe';
    const tr = fit(ctx, c.translation!, (s) => latinFont(s), 34, 20, textWidth, 330, 1.45);
    ctx.font = latinFont(tr.size);
    y = 830 + tr.size;
    for (const line of tr.lines) {
      ctx.fillText(line, W / 2, y);
      y += tr.size * 1.45;
    }
    if (c.translationSource) {
      ctx.font = latinFont(20);
      ctx.fillStyle = 'rgba(224, 242, 254, 0.7)';
      ctx.fillText(c.translationSource, W / 2, Math.min(y + 14, 1190));
    }
  }

  // Reference and attribution
  ctx.direction = 'ltr';
  ctx.fillStyle = '#fde68a';
  ctx.font = latinFont(34, 600);
  ctx.fillText(c.reference, W / 2, 1235);
  ctx.font = latinFont(20);
  ctx.fillStyle = 'rgba(255, 255, 255, 0.65)';
  ctx.fillText('Qur’an text: Tanzil Project · tanzil.net · CC BY 3.0   |   Tadabbur', W / 2, 1280);

  return await new Promise<Blob>((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('encoding failed'))), 'image/png'));
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '');
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

export async function shareVerseImage(c: VerseImageContent, fileName: string): Promise<'shared' | 'downloaded' | 'failed'> {
  try {
    const blob = await renderVerseImage(c);
    if (isNativeApp) {
      const [{ Filesystem, Directory }, { Share }] = await Promise.all([
        import('@capacitor/filesystem'),
        import('@capacitor/share'),
      ]);
      const written = await Filesystem.writeFile({
        path: fileName, data: await blobToBase64(blob), directory: Directory.Cache,
      });
      await Share.share({ title: c.reference, files: [written.uri] });
      return 'shared';
    }
    const file = new File([blob], fileName, { type: 'image/png' });
    if (navigator.canShare?.({ files: [file] })) {
      await navigator.share({ files: [file], title: c.reference });
      return 'shared';
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
    return 'downloaded';
  } catch {
    return 'failed';
  }
}
