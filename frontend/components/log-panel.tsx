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
      "Herkesin gördüğü ürünlere değil, daha ilginç adaylara bakıyorum.",
      "Herkesin gördüğü ürünler yerine daha ilginç adaylar öne çıkarıldı.",
    ],
    [
      "Bulduğumuz adayları tartıp en yerinde üçlüyü seçiyorum.",
      "Adaylar değerlendirildi ve en yerinde üçlü belirlendi.",
    ],
  ];

  return replacements.find(([from]) => from === message)?.[1] ?? message;
}

export function LogPanel({ logs, statusMessage, status }: LogPanelProps) {
  return (
    <section className="sticky top-6 relative min-h-[320px] overflow-hidden rounded-[28px] border border-stone-200 p-6">
      <div className="mb-5 flex items-center justify-between border-b border-stone-200 pb-4">
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">Canlı Notlar</p>
          <p className="mt-1 text-sm text-stone-500">{statusMessage}</p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-stone-200 bg-[#f8f8f6] text-navy">
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
            className="animate-rise rounded-[22px] border border-stone-200 bg-[linear-gradient(180deg,rgba(251,251,250,0.96),rgba(246,246,243,0.92))] px-4 py-4 shadow-[0_8px_22px_rgba(15,23,42,0.03)]"
            style={{ animationDelay: `${index * 120}ms` }}
          >
            <p className="text-xs text-stone-400">
              {log.agent}
            </p>
            {log.role ? (
              <p className="mt-1 text-xs text-stone-400">{log.role}</p>
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
