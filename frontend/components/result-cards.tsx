import { ArrowUpRight } from "lucide-react";

import { ProductCard } from "@/lib/types";

type ResultCardsProps = {
  intro: string;
  products: ProductCard[];
};

type ProductItemProps = {
  product: ProductCard;
  index: number;
  featured?: boolean;
};

function ProductItem({ product, index, featured = false }: ProductItemProps) {
  return (
    <article
      className={`animate-fade-slide flex flex-col justify-between rounded-[28px] border border-stone-200 bg-white p-6 shadow-[0_14px_32px_rgba(15,23,42,0.045)] ${
        featured ? "min-h-[300px] lg:p-8" : "min-h-[340px]"
      }`}
      style={{ animationDelay: `${index * 110}ms` }}
    >
      <div>
        <div className="flex items-start border-b border-stone-100 pb-4">
          <p className="rounded-full bg-stone-100 px-3 py-1 text-[11px] font-medium tracking-[0.14em] text-stone-500">
            {product.source}
          </p>
        </div>
        <h3
          className={`mt-5 font-semibold leading-[1.14] tracking-[-0.03em] text-stone-900 ${
            featured
              ? "max-w-[20ch] text-[1.55rem] sm:text-[1.85rem]"
              : "max-w-[16ch] text-[1.2rem] sm:text-[1.35rem]"
          }`}
        >
          {product.name}
        </h3>
        <p
          className={`mt-4 text-stone-600 ${
            featured ? "max-w-3xl text-[1rem] leading-8" : "text-[15px] leading-7"
          }`}
        >
          {product.why_it_matches}
        </p>
      </div>

      <div
        className={`mt-8 flex border-t border-stone-300 pt-5 ${
          featured
            ? "flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"
            : "items-end justify-between gap-4"
        }`}
      >
        <div>
          <p className="text-xs text-stone-400">Fiyat</p>
          <p className="mt-1 text-base font-medium text-stone-800">{product.price_label}</p>
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
  );
}

export function ResultCards({ intro, products }: ResultCardsProps) {
  const [featuredProduct, ...secondaryProducts] = products;

  return (
    <section className="space-y-6">
      <div className="animate-soft-in overflow-hidden rounded-[30px] border border-stone-200">
        <div className="border-b border-stone-200 bg-[linear-gradient(180deg,rgba(243,247,253,0.95),rgba(255,255,255,0.94))] px-6 py-6">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs text-stone-400">Genel Değerlendirme</p>
          </div>
          <h2 className="mt-4 max-w-5xl text-[1.35rem] font-semibold leading-[1.35] tracking-[-0.03em] text-navy sm:text-[1.6rem]">
            {intro}
          </h2>
        </div>
      </div>

      <div className="space-y-5">
        {featuredProduct ? <ProductItem product={featuredProduct} index={0} featured /> : null}

        {secondaryProducts.length ? (
          <div className="grid gap-5 lg:grid-cols-2">
            {secondaryProducts.map((product, index) => (
              <ProductItem key={`${product.name}-${index}`} product={product} index={index + 1} />
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
