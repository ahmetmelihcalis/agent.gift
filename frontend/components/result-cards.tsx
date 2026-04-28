import { ArrowUpRight } from "lucide-react";

import { ProductCard } from "@/lib/types";

type ResultCardsProps = {
  intro: string;
  products: ProductCard[];
};

export function ResultCards({ intro, products }: ResultCardsProps) {
  return (
    <section className="space-y-6">
      <div className="animate-soft-in overflow-hidden rounded-[28px] border border-stone-300 bg-white/90 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
        <div className="border-b border-stone-300 bg-[linear-gradient(180deg,rgba(244,247,252,0.9),rgba(255,255,255,0.92))] px-6 py-6">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs tracking-[0.16em] text-stone-400">
              Genel Değerlendirme
            </p>
          </div>
          <h2 className="mt-4 max-w-5xl text-[1.35rem] font-semibold leading-[1.35] tracking-[-0.03em] text-navy sm:text-[1.6rem]">
            {intro}
          </h2>
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-2 2xl:grid-cols-3">
        {products.map((product, index) => (
          <article
            key={product.name}
            className="animate-fade-slide flex min-h-[340px] flex-col justify-between rounded-[28px] border border-stone-300 bg-white p-6 shadow-[0_10px_30px_rgba(15,23,42,0.05)]"
            style={{ animationDelay: `${index * 110}ms` }}
          >
            <div>
              <div className="flex items-start border-b border-stone-100 pb-4">
                <p className="text-[11px] tracking-[0.16em] text-stone-400">
                  {product.source}
                </p>
              </div>
              <h3 className="mt-5 max-w-[16ch] text-[1.2rem] font-semibold leading-[1.18] tracking-[-0.03em] text-stone-900 sm:text-[1.35rem]">
                {product.name}
              </h3>
              <p className="mt-4 text-[15px] leading-8 text-stone-600">
                {product.why_it_matches}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {product.matched_signals.map((signal) => (
                  <span
                    key={signal}
                    className="rounded-full bg-stone-100 px-3 py-1 text-xs text-stone-600"
                  >
                    {signal}
                  </span>
                ))}
              </div>
              <p className="mt-5 border-l border-stone-300 pl-4 text-sm italic leading-7 text-stone-500">
                {product.editorial_note}
              </p>
              <p className="mt-4 text-sm leading-7 text-stone-500">
                {product.comparison_note}
              </p>
              {product.caveats.length > 0 ? (
                <div className="mt-5 rounded-2xl bg-stone-50 px-4 py-3">
                  <p className="text-xs tracking-[0.16em] text-stone-400">
                    Not Düşelim
                  </p>
                  <div className="mt-2 space-y-1">
                    {product.caveats.map((caveat) => (
                      <p key={caveat} className="text-sm leading-6 text-stone-500">
                        {caveat}
                      </p>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="mt-8 flex items-end justify-between gap-4 border-t border-stone-300 pt-5">
              <div>
                <p className="text-xs tracking-[0.16em] text-stone-400">
                  Fiyat
                </p>
                <p className="mt-1 text-base font-medium text-stone-800">
                  {product.price_label}
                </p>
              </div>

              <a
                href={product.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-4 py-2 text-sm text-navy transition hover:border-[#1f3a68] hover:bg-[#1f3a68] hover:text-white"
              >
                İncele
                <ArrowUpRight className="h-4 w-4" />
              </a>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
