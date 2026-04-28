"use client";

export function ResultSkeleton() {
  return (
    <section className="space-y-6 animate-soft-in">
      <div className="overflow-hidden rounded-[28px] border border-[#1f3a68] bg-white/90 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
        <div className="border-b border-[#1f3a68] px-6 py-6">
          <div className="skeleton h-4 w-36 rounded-full" />
          <div className="mt-4 skeleton h-12 w-full rounded-[20px]" />
          <div className="mt-3 skeleton h-12 w-4/5 rounded-[20px]" />
        </div>
        <div className="grid gap-5 px-6 py-6 lg:grid-cols-[1.35fr_0.65fr]">
          <div className="rounded-[24px] border border-[#1f3a68] bg-white/90 px-5 py-5">
            <div className="skeleton h-4 w-32 rounded-full" />
            <div className="mt-4 space-y-3">
              <div className="skeleton h-4 w-full rounded-full" />
              <div className="skeleton h-4 w-11/12 rounded-full" />
              <div className="skeleton h-4 w-10/12 rounded-full" />
            </div>
          </div>
          <div className="rounded-[24px] border border-[#1f3a68] bg-white/90 px-5 py-5">
            <div className="skeleton h-4 w-24 rounded-full" />
            <div className="mt-4 space-y-3">
              <div className="skeleton h-4 w-full rounded-full" />
              <div className="skeleton h-4 w-4/5 rounded-full" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <article
            key={index}
            className="rounded-[28px] border border-[#1f3a68] bg-white/90 p-6 shadow-[0_10px_30px_rgba(15,23,42,0.05)]"
          >
            <div className="skeleton h-4 w-24 rounded-full" />
            <div className="mt-4 skeleton h-9 w-4/5 rounded-[16px]" />
            <div className="mt-5 space-y-3">
              <div className="skeleton h-4 w-full rounded-full" />
              <div className="skeleton h-4 w-11/12 rounded-full" />
              <div className="skeleton h-4 w-9/12 rounded-full" />
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <div className="skeleton h-8 w-24 rounded-full" />
              <div className="skeleton h-8 w-20 rounded-full" />
            </div>
            <div className="mt-6 skeleton h-20 w-full rounded-[18px]" />
          </article>
        ))}
      </div>
    </section>
  );
}

export function PanelSkeleton() {
  return (
    <div className="space-y-4 animate-soft-in">
      {Array.from({ length: 3 }).map((_, index) => (
        <div
          key={index}
          className="rounded-[24px] border border-[#1f3a68] bg-white/90 px-5 py-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]"
        >
          <div className="skeleton h-4 w-32 rounded-full" />
          <div className="mt-4 space-y-3">
            <div className="skeleton h-4 w-full rounded-full" />
            <div className="skeleton h-4 w-5/6 rounded-full" />
            <div className="skeleton h-4 w-4/6 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
