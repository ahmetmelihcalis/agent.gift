"use client";

import { useState, useTransition } from "react";
import { ArrowRight, Search, Sparkles } from "lucide-react";

import { AgentRoster } from "@/components/agent-roster";
import { PanelSkeleton, ResultSkeleton } from "@/components/loading-skeletons";
import { LogPanel } from "@/components/log-panel";
import { ResultCards } from "@/components/result-cards";
import { streamInvestigate } from "@/lib/streamInvestigate";
import {
  AgentState,
  InvestigationResult,
  InvestigatePayload,
  StreamLog,
  StreamStatus,
} from "@/lib/types";

const initialBrief =
  "Hedef kişinin davranışsal özelliklerini ve ilgi alanlarını belirtin. İlgi alanları, sahip olduğu hobiler veya kaçındığı şeyler gibi detayları girin.";

const MIN_BRIEF_LENGTH = 10;

const defaultAgents: AgentState[] = [
  {
    id: "profile_analyst",
    name: "The Analyst",
    role: "Profil Analisti Ajan",
    specialty:
      "Girilen metni işleyerek hedef kişinin davranışsal eğilimlerini ve ilgi alanı kategorilerini belirler.",
    status: "idle",
    headline: "",
  },
  {
    id: "product_hunter",
    name: "Finder Fox",
    role: "Ürün Tarama Ajanı",
    specialty:
      "Standart seçenekleri filtreler. Çıkarılan profile uygun, özgün ve erişilebilir ürün alternatiflerini tarar.",
    status: "idle",
    headline: "",
  },
  {
    id: "gift_selector",
    name: "Mr. Decision",
    role: "Değerlendirme ve Raporlama Ajanı",
    specialty:
      "Belirlenen adayları uygunluk ve profil eşleşmesi metriklerine göre inceler. En yüksek skora sahip üç öneriyi gerekçelendirerek sunar.",
    status: "idle",
    headline: "",
  },
];

const refineOptions = ["Spesifik", "Bütçe Dostu", "Üst Segment", "Eğlence"];

export default function HomePage() {
  const [brief, setBrief] = useState("");
  const [logs, setLogs] = useState<StreamLog[]>([]);
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [statusMessage, setStatusMessage] = useState("Henüz bir araştırma başlamadı.");
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [agents, setAgents] = useState<AgentState[]>(defaultAgents);
  const [activeRefineInstruction, setActiveRefineInstruction] = useState("");
  const [isPending, startTransition] = useTransition();

  const buildPayload = (nextBrief: string, refineInstruction = ""): InvestigatePayload => ({
    brief: nextBrief,
    refine_instruction: refineInstruction || undefined,
  });

  const startInvestigation = (refineInstruction = "") => {
    const trimmed = brief.trim();
    if (!trimmed) {
      setErrorMessage("Sistemin çalışabilmesi için biraz daha açık bir tarif gerekli.");
      return;
    }

    if (trimmed.length < MIN_BRIEF_LENGTH) {
      setErrorMessage("Biraz daha detay gerekli. En az 10 karakterlik bir tarif yaz.");
      return;
    }

    const payload = buildPayload(trimmed, refineInstruction);
    setActiveRefineInstruction(refineInstruction);
    setLogs([]);
    setResult(null);
    setErrorMessage("");
    setStatus("streaming");
    setStatusMessage("Dosya açılıyor.");
    setAgents(defaultAgents);

    startTransition(() => {
      void (async () => {
        let receivedResult = false;
        let receivedError = false;

        try {
          await streamInvestigate(payload, (event) => {
            if (event.event === "status") {
              setStatusMessage(event.data.message);
            }

            if (event.event === "agents") {
              setAgents(event.data.agents);
            }

            if (event.event === "log") {
              setLogs((current) => [...current, event.data]);
            }

            if (event.event === "result") {
              receivedResult = true;
              setResult(event.data);
              setAgents(event.data.agents);
              setStatus("success");
              setStatusMessage("Öneriler hazır.");
            }

            if (event.event === "error") {
              receivedError = true;
              setStatus("error");
              setErrorMessage(event.data.detail || event.data.message);
              setStatusMessage("Araştırma akışı durdu.");
            }
          });

          if (!receivedResult && !receivedError) {
            setStatus("error");
            setErrorMessage("Sistem bu turda net bir öneri çıkaramadı.");
            setStatusMessage("Araştırma akışı durdu.");
          }
        } catch (error) {
          setStatus("error");
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Sistem şu an yanıt veremiyor. Biraz sonra tekrar deneyin.",
          );
          setStatusMessage("Araştırma akışı durdu.");
        }
      })();
    });
  };

  return (
    <main className="min-h-screen">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-8 sm:px-10">
        <header className="flex items-center justify-between border-b border-stone-300 pb-6">
          <div>
            <h1 className="text-[2rem] font-semibold tracking-[-0.04em] text-stone-900">
              agent.gift
            </h1>
            <p className="mt-1 text-sm text-stone-500">
              Yapay Zeka Ajanları Tabanlı Hediye Öneri Sistemi
            </p>
          </div>
        </header>

        <section className="flex flex-1 flex-col gap-10 py-10 lg:gap-12">
          <div className="space-y-8">
            <div className="mx-auto max-w-5xl space-y-4 text-center">
              <h2 className="mx-auto max-w-4xl text-[2.45rem] font-semibold leading-[1.05] tracking-[-0.05em] text-navy sm:text-[2.9rem]">
                Hedef profile uyumlu hediye öneri sistemi.
              </h2>
              <p className="mx-auto max-w-3xl text-[1rem] leading-8 text-stone-600">
                agent.gift, sağlanan profile göre kişiselleştirilmiş ve spesifik
                hediye önerileri üretir, sürecin her adımını görünür kılar.
              </p>
              <div className="grid gap-4 text-left sm:grid-cols-3">
                <div className="rounded-[22px] border border-stone-300 bg-white/80 px-4 py-4 shadow-[0_10px_30px_rgba(15,23,42,0.04)]">
                  <p className="text-[11px] tracking-[0.16em] text-stone-400">1. Adım</p>
                  <p className="mt-2 text-sm leading-6 text-stone-700">Profil okunur ve öne çıkan davranış sinyalleri ayrıştırılır.</p>
                </div>
                <div className="rounded-[22px] border border-stone-300 bg-white/80 px-4 py-4 shadow-[0_10px_30px_rgba(15,23,42,0.04)]">
                  <p className="text-[11px] tracking-[0.16em] text-stone-400">2. Adım</p>
                  <p className="mt-2 text-sm leading-6 text-stone-700">Standart seçenekler elenir, profile uygun adaylar taranır.</p>
                </div>
                <div className="rounded-[22px] border border-stone-300 bg-white/80 px-4 py-4 shadow-[0_10px_30px_rgba(15,23,42,0.04)]">
                  <p className="text-[11px] tracking-[0.16em] text-stone-400">3. Adım</p>
                  <p className="mt-2 text-sm leading-6 text-stone-700">En güçlü öneriler kısa ve anlaşılır gerekçelerle sunulur.</p>
                </div>
              </div>
            </div>

            <section className="rounded-[28px] border border-stone-300 bg-white/95 p-3 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
              <div className="rounded-[22px] border border-stone-300 bg-[#fcfcfb]">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-300 px-5 py-4">
                  <div>
                    <p className="text-sm font-medium text-stone-700">Yeni Araştırma</p>
                    <p className="mt-1 text-sm text-stone-500">
                      Hedef profilin belirgin özelliklerini sisteme girin.
                    </p>
                  </div>
                  <span className="rounded-full bg-stone-100 px-3 py-1 text-xs text-stone-500">
                    Tek komut, çoklu ajan mimarisi
                  </span>
                </div>

                <textarea
                  value={brief}
                  onChange={(event) => setBrief(event.target.value)}
                  placeholder={initialBrief}
                  className="min-h-[220px] w-full resize-none border-none bg-transparent px-5 py-5 font-sans text-[1rem] leading-8 text-stone-800 outline-none placeholder:text-stone-400"
                />

                <div className="flex flex-wrap gap-2 px-5 pb-2">
                  {refineOptions.map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => setActiveRefineInstruction(item)}
                      className={`rounded-full border px-3 py-2 text-sm transition ${
                        activeRefineInstruction === item
                          ? "border-[#1f3a68] bg-[#1f3a68] text-white"
                          : "border-stone-300 bg-white text-stone-600"
                      }`}
                    >
                      {item}
                    </button>
                  ))}
                </div>

                <div className="flex flex-col gap-4 border-t border-stone-300 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="max-w-xl space-y-1 text-sm leading-6 text-stone-500">
                    <p>Daha isabetli sonuçlar için ilgi alanları ve kaçınılan şeyleri birlikte yazın.</p>
                    {activeRefineInstruction ? (
                      <p className="text-navy">Aktif yönlendirme: {activeRefineInstruction}</p>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-stone-400">{brief.trim().length} karakter</span>
                    <button
                      type="button"
                      onClick={() => startInvestigation(activeRefineInstruction)}
                      disabled={isPending || status === "streaming"}
                      className="inline-flex items-center justify-center gap-2 rounded-full bg-[#1f3a68] px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-[#193257] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <Search className="h-4 w-4" />
                      Araştır
                    </button>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <section className="grid gap-8 lg:grid-cols-[0.88fr_1.12fr] lg:items-start lg:gap-10">
            <aside className="space-y-6 lg:sticky lg:top-6">
              <div className="rounded-[32px] border border-stone-400 bg-[linear-gradient(180deg,rgba(248,248,246,0.88),rgba(255,255,255,0.96))] p-5 shadow-[0_14px_40px_rgba(15,23,42,0.05)] backdrop-blur-sm">
                <div className="mb-5 flex items-center justify-between border-b border-stone-400 pb-4">
                  <div>
                    <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">
                      Operasyon Paneli
                    </p>
                  </div>
                </div>

                <div className="space-y-6">
                  {status === "streaming" && logs.length === 0 ? (
                    <PanelSkeleton />
                  ) : (
                    <AgentRoster agents={agents} />
                  )}
                  <div className="transition-all duration-300 ease-out">
                    <LogPanel logs={logs} statusMessage={statusMessage} status={status} />
                  </div>
                </div>
              </div>
            </aside>

            <div className="space-y-6">
              {errorMessage ? (
                <div className="rounded-[24px] border border-stone-400 bg-stone-100/80 p-5 text-sm leading-7 text-stone-700">
                  <div className="flex items-center gap-3 text-navy">
                    <Sparkles className="h-4 w-4" />
                    <span className="font-medium">Sistem şu an sonuç üretemedi.</span>
                  </div>
                  <p className="mt-2">{errorMessage}</p>
                </div>
              ) : null}

              {result ? (
                <div className="space-y-6">
                  <section className="animate-soft-in rounded-[28px] border border-stone-300 bg-white/90 p-6 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="text-xs tracking-[0.18em] text-stone-400">
                        Profil Özeti
                      </p>
                      <span className="rounded-full border border-stone-300 px-3 py-1 text-xs text-stone-500">
                        {result.profile_snapshot.inferred_persona}
                      </span>
                    </div>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div>
                        <p className="text-xs tracking-[0.18em] text-stone-400">
                          Öne Çıkan İlgi Alanları
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {result.profile_snapshot.obsessions.map((item) => (
                            <span
                              key={item}
                              className="rounded-full bg-stone-100 px-3 py-1 text-xs text-stone-600"
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-xs tracking-[0.18em] text-stone-400">
                          İnce İpuçları
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {result.profile_snapshot.hidden_hooks.map((item) => (
                            <span
                              key={item}
                              className="rounded-full bg-[#eef3fb] px-3 py-1 text-xs text-navy"
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </section>

                  <ResultCards
                    intro={result.editorial_intro}
                    products={result.products}
                  />
                </div>
              ) : status === "streaming" ? (
                <ResultSkeleton />
              ) : (
                <section className="rounded-[28px] border border-dashed border-stone-300 bg-white/60 p-6">
                  <div className="flex items-center gap-3 text-navy">
                    <ArrowRight className="h-4 w-4" />
                    <p className="font-medium">İşlem sonuçları bu alanda listelenecektir.</p>
                  </div>
                  <p className="mt-3 max-w-2xl text-sm leading-7 text-stone-500">
                    Süreç tamamlandığında; önerilen ürünler, eşleşme kriterleri ve
                    sistem notlarıyla birlikte raporlanır.
                  </p>
                </section>
              )}
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}
