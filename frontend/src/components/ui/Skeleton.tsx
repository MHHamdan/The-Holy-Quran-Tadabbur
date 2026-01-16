/**
 * Skeleton - Production-grade loading skeleton components
 *
 * Features:
 * - Customizable shapes (text, circle, rectangle)
 * - Animation variants (pulse, wave)
 * - Accessible with aria-busy
 * - Composable for complex layouts
 */

import clsx from 'clsx';
import { memo } from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
  lines?: number;
}

export const Skeleton = memo(function Skeleton({
  className,
  variant = 'text',
  width,
  height,
  animation = 'pulse',
  lines = 1,
}: SkeletonProps) {
  const baseClasses = clsx(
    'bg-gray-200',
    animation === 'pulse' && 'animate-pulse',
    animation === 'wave' && 'animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]',
    variant === 'text' && 'h-4 rounded',
    variant === 'circular' && 'rounded-full',
    variant === 'rectangular' && 'rounded-none',
    variant === 'rounded' && 'rounded-lg',
    className
  );

  const style: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  if (lines > 1) {
    return (
      <div className="space-y-2" role="status" aria-busy="true" aria-label="Loading">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={baseClasses}
            style={{
              ...style,
              width: i === lines - 1 ? '75%' : style.width,
            }}
          />
        ))}
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  return (
    <div
      className={baseClasses}
      style={style}
      role="status"
      aria-busy="true"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
});

// Pre-built skeleton compositions
export const SkeletonCard = memo(function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={clsx('p-4 bg-white border border-gray-200 rounded-lg', className)}
      role="status"
      aria-busy="true"
      aria-label="Loading card"
    >
      <div className="flex items-start gap-4">
        <Skeleton variant="rounded" width={48} height={48} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" height={20} />
          <Skeleton variant="text" width="100%" />
          <Skeleton variant="text" width="80%" />
        </div>
      </div>
      <span className="sr-only">Loading...</span>
    </div>
  );
});

export const SkeletonTable = memo(function SkeletonTable({
  rows = 5,
  columns = 4,
  className,
}: {
  rows?: number;
  columns?: number;
  className?: string;
}) {
  return (
    <div className={clsx('space-y-3', className)} role="status" aria-busy="true" aria-label="Loading table">
      {/* Header */}
      <div className="flex gap-4 pb-2 border-b border-gray-200">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} variant="text" className="flex-1" height={16} />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div key={rowIdx} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIdx) => (
            <Skeleton key={colIdx} variant="text" className="flex-1" />
          ))}
        </div>
      ))}
      <span className="sr-only">Loading...</span>
    </div>
  );
});

export const SkeletonList = memo(function SkeletonList({
  count = 5,
  className,
}: {
  count?: number;
  className?: string;
}) {
  return (
    <div className={clsx('space-y-4', className)} role="status" aria-busy="true" aria-label="Loading list">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
      <span className="sr-only">Loading...</span>
    </div>
  );
});

// Prayer times specific skeleton
export const SkeletonPrayerTimes = memo(function SkeletonPrayerTimes() {
  return (
    <div className="space-y-4" role="status" aria-busy="true" aria-label="Loading prayer times">
      {/* Location */}
      <div className="flex items-center gap-2">
        <Skeleton variant="circular" width={20} height={20} />
        <Skeleton variant="text" width="40%" />
      </div>

      {/* Prayer grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="p-4 bg-white border border-gray-200 rounded-lg">
            <Skeleton variant="text" width="50%" className="mb-2" />
            <Skeleton variant="text" width="70%" height={24} />
          </div>
        ))}
      </div>
      <span className="sr-only">Loading...</span>
    </div>
  );
});

// Calendar specific skeleton
export const SkeletonCalendar = memo(function SkeletonCalendar() {
  return (
    <div className="space-y-4" role="status" aria-busy="true" aria-label="Loading calendar">
      {/* Header */}
      <div className="flex justify-between items-center">
        <Skeleton variant="rounded" width={32} height={32} />
        <Skeleton variant="text" width="30%" height={24} />
        <Skeleton variant="rounded" width={32} height={32} />
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} variant="text" height={20} />
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: 35 }).map((_, i) => (
          <Skeleton key={i} variant="rounded" height={40} />
        ))}
      </div>
      <span className="sr-only">Loading...</span>
    </div>
  );
});
