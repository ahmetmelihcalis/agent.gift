"use client";

import { FileSearch } from "lucide-react";

import { StreamLog } from "@/lib/types";

type LogPanelProps = {
  logs: StreamLog[];
  statusMessage: string;
  status: "idle" | "streaming" | "success" | "error";
};

function finalizeMessage(message: string) {
  const replacements: Array<[string, string]> = [
    [
      "Anlatılanların arasından kişinin asıl eğilimlerini ayıklıyorum.",
      "Anlatılanların arasından kişinin asıl eğilimleri ayıklandı.",
    ],
    [
      "Herkesin gördüğü ürünlere değil, daha ilginç ürünlere bakıyorum.",
      "Herkesin gördüğü ürünler yerine daha ilginç ürünler öne çıkarıldı.",
    ],
    [
      "Bulduğumuz ürünleri tartıp en yerinde üçlüyü seçiyorum.",
      "Ürünler değerlendirildi ve en yerinde üçlü belirlendi.",
    ],
  ];

  return replacements.find(([from]) => from === message)?.[1] ?? message;
}

export function LogPanel({ logs, statusMessage, status }: LogPanelProps) {
  return (
    <section className="sticky top-6 relative min-h-[320px] overflow-hidden rounded-[28px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(244,248,255,0.54),rgba(255,255,255,0.9))] p-6 shadow-[0_14px_32px_rgba(31,58,104,0.07)]">
      <div className="mb-5 flex items-center justify-between border-b border-[#1f3a68] pb-4">
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">Canlı Notlar</p>
          <p className="mt-1 text-sm text-stone-500">{statusMessage}</p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-[#1f3a68] bg-[#e7f0ff] text-navy">
          <FileSearch className="h-5 w-5" />
        </div>
      </div>

      <div className="space-y-4">
        {logs.length === 0 ? (
          <p className="max-w-md text-sm leading-7 text-stone-500">
            Araştırma başladığında ajanın bıraktığı notlar burada akacak.
          </p>
        ) : null}

        {logs.map((log, index) => (
          <article
            key={`${log.agent}-${index}`}
            className="animate-rise rounded-[22px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(238,245,255,0.84),rgba(255,255,255,0.98))] px-4 py-4 shadow-[0_10px_24px_rgba(31,58,104,0.05)]"
            style={{ animationDelay: `${index * 120}ms` }}
          >
            <p className="text-xs font-medium text-navy">
              {log.agent}
            </p>
            {log.role ? (
              <p className="mt-1 text-xs font-medium text-navy">{log.role}</p>
            ) : null}
            <p className="mt-2 text-sm leading-7 text-stone-700">
              {status === "success" ? finalizeMessage(log.message) : log.message}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
