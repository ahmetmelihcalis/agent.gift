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

function shoppingHint(source: string) {
  return `${source} içinde benzer ürünlere bakılabilir.`;
}

function ProductItem({ product, index, featured = false }: ProductItemProps) {
  return (
    <article
      className={`animate-fade-slide flex flex-col justify-between rounded-[28px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(239,246,255,0.82),rgba(255,255,255,0.98))] p-6 shadow-[0_16px_34px_rgba(31,58,104,0.08)] ${
        featured ? "min-h-[300px] lg:p-8" : "min-h-[340px]"
      }`}
      style={{ animationDelay: `${index * 110}ms` }}
    >
      <div>
        <div className="flex items-start border-b border-[#1f3a68] pb-4">
          <p className="rounded-full border border-[#1f3a68] bg-[#e8f1ff] px-3 py-1 text-[11px] font-medium tracking-[0.14em] text-navy">
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
            featured ? "max-w-3xl text-[0.96rem] leading-7" : "text-[14px] leading-7"
          }`}
        >
          {product.why_it_matches}
        </p>
      </div>

      <div
        className={`mt-8 border-t border-[#1f3a68] pt-5 ${
          featured ? "grid gap-4 sm:grid-cols-2" : "grid gap-4"
        }`}
      >
        <div>
          <p className="text-xs font-medium text-navy">Fiyat</p>
          <p className="mt-1 text-base font-medium text-stone-800">{product.price_label}</p>
        </div>

        <div>
          <p className="text-xs font-medium text-navy">Bakılabilecek yer</p>
          <p className="mt-1 text-sm leading-6 text-stone-700">{shoppingHint(product.source)}</p>
        </div>
      </div>
    </article>
  );
}

export function ResultCards({ intro, products }: ResultCardsProps) {
  const [featuredProduct, ...secondaryProducts] = products;

  return (
    <section className="space-y-6">
      <div className="animate-soft-in overflow-hidden rounded-[30px] border border-[#1f3a68] shadow-[0_18px_38px_rgba(31,58,104,0.08)]">
        <div className="border-b border-[#1f3a68] bg-[linear-gradient(180deg,rgba(230,239,255,0.92),rgba(255,255,255,0.95))] px-6 py-6">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">Genel Değerlendirme</p>
          </div>
          <h2 className="mt-4 max-w-5xl text-[1.12rem] font-semibold leading-[1.45] tracking-[-0.02em] text-navy sm:text-[1.28rem]">
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
