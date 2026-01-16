/**
 * Skeleton Loader Components
 *
 * Provides loading state placeholders for:
 * - Concept cards
 * - Miracle cards
 * - List items
 * - Detail pages
 */
import clsx from 'clsx';

interface SkeletonProps {
  className?: string;
}

export function SkeletonPulse({ className }: SkeletonProps) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-gray-200 rounded',
        className
      )}
    />
  );
}

export function ConceptCardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
      <div className="flex items-center gap-3">
        <SkeletonPulse className="w-10 h-10 rounded-lg" />
        <div className="flex-1 space-y-2">
          <SkeletonPulse className="h-4 w-3/4" />
          <SkeletonPulse className="h-3 w-1/2" />
        </div>
      </div>
      <SkeletonPulse className="h-3 w-full" />
      <div className="flex gap-2">
        <SkeletonPulse className="h-6 w-16 rounded-full" />
        <SkeletonPulse className="h-6 w-20 rounded-full" />
      </div>
    </div>
  );
}

export function MiracleCardSkeleton() {
  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200 p-4 space-y-3">
      <div className="flex items-start gap-3">
        <SkeletonPulse className="w-10 h-10 rounded-lg bg-amber-200" />
        <div className="flex-1 space-y-2">
          <SkeletonPulse className="h-5 w-3/4 bg-amber-200" />
          <SkeletonPulse className="h-4 w-1/2 bg-amber-100" />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <SkeletonPulse className="h-4 w-12 bg-amber-100" />
        <SkeletonPulse className="h-4 w-12 bg-amber-100" />
        <SkeletonPulse className="h-4 w-16 bg-amber-100" />
      </div>
    </div>
  );
}

export function ConceptDetailSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-6">
        <div className="flex items-start gap-4">
          <SkeletonPulse className="w-14 h-14 rounded-xl" />
          <div className="flex-1 space-y-3">
            <SkeletonPulse className="h-7 w-1/2" />
            <SkeletonPulse className="h-5 w-1/3" />
            <SkeletonPulse className="h-4 w-full" />
            <SkeletonPulse className="h-4 w-2/3" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200 pb-2">
        <SkeletonPulse className="h-8 w-32" />
        <SkeletonPulse className="h-8 w-32" />
      </div>

      {/* Content */}
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <SkeletonPulse key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}

export function ListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonPulse key={i} className="h-12 w-full rounded-lg" />
      ))}
    </div>
  );
}

export function ConceptGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <ConceptCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function MiracleGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <MiracleCardSkeleton key={i} />
      ))}
    </div>
  );
}
