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
      "Belirlenen ürünleri uygunluk ve profil eşleşmesi metriklerine göre inceler. En yüksek skora sahip üç öneriyi gerekçelendirerek sunar.",
    status: "idle",
    headline: "",
  },
];

const refineOptions = ["Spesifik", "Bütçe Dostu", "Üst Segment", "Eğlence"] as const;

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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(224,231,255,0.28),transparent_34%),linear-gradient(180deg,#fbfbf9_0%,#f6f5f1_100%)]">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-10 sm:px-10">
        <header className="flex items-center justify-between border-b border-[#1f3a68] pb-8 bg-[linear-gradient(180deg,rgba(244,248,255,0.35),rgba(255,255,255,0))]">
          <div>
            <h1 className="text-[2rem] font-semibold tracking-[-0.04em] text-stone-900">
              agent.gift
            </h1>
            <p className="mt-1 text-sm leading-6 text-navy/75">
              Yapay Zeka Ajanları Tabanlı Hediye Öneri Sistemi
            </p>
          </div>
        </header>

        <section className="flex flex-1 flex-col gap-12 py-10 lg:gap-14">
          <div className="space-y-10">
            <div className="mx-auto max-w-5xl space-y-5 text-center">
              <h2 className="mx-auto max-w-4xl text-[2.55rem] font-semibold leading-[1.02] tracking-[-0.06em] text-navy sm:text-[3.05rem]">
                Hedef profile uyumlu hediye öneri sistemi.
              </h2>
              <p className="mx-auto max-w-3xl text-[1.02rem] leading-8 text-stone-600 sm:text-[1.05rem]">
                agent.gift, sağlanan profile göre kişiselleştirilmiş ve spesifik
                hediye önerileri üretir, sürecin her adımını görünür kılar.
              </p>
              <div className="grid gap-4 text-left sm:grid-cols-3">
                <div className="rounded-[24px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(233,241,255,0.95),rgba(255,255,255,0.96))] px-5 py-5 shadow-[0_16px_34px_rgba(31,58,104,0.08)] backdrop-blur-sm">
                  <p className="text-[2.2rem] font-semibold tracking-[-0.04em] text-navy">1. Adım</p>
                  <p className="mt-3 text-[0.96rem] leading-6 text-stone-700">Profil okunur ve öne çıkan davranış sinyalleri ayrıştırılır.</p>
                </div>
                <div className="rounded-[24px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(233,241,255,0.95),rgba(255,255,255,0.96))] px-5 py-5 shadow-[0_16px_34px_rgba(31,58,104,0.08)] backdrop-blur-sm">
                  <p className="text-[2.2rem] font-semibold tracking-[-0.04em] text-navy">2. Adım</p>
                  <p className="mt-3 text-[0.96rem] leading-6 text-stone-700">Standart seçenekler elenir, uygun ürünler taranır.</p>
                </div>
                <div className="rounded-[24px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(233,241,255,0.95),rgba(255,255,255,0.96))] px-5 py-5 shadow-[0_16px_34px_rgba(31,58,104,0.08)] backdrop-blur-sm">
                  <p className="text-[2.2rem] font-semibold tracking-[-0.04em] text-navy">3. Adım</p>
                  <p className="mt-3 text-[0.96rem] leading-6 text-stone-700">En güçlü öneriler kısa ve anlaşılır gerekçelerle sunulur.</p>
                </div>
              </div>
            </div>

            <section className="rounded-[32px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(241,246,255,0.52),rgba(255,255,255,0.82))] p-3 shadow-[0_18px_38px_rgba(31,58,104,0.08)] backdrop-blur-sm">
              <div className="overflow-hidden rounded-[28px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,255,0.96))]">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1f3a68] px-6 py-5">
                  <div className="max-w-3xl">
                    <p className="text-[2.2rem] font-semibold tracking-[-0.04em] text-navy">Yeni Araştırma</p>
                    <p className="mt-1 text-sm text-stone-500">
                      Hedef profilin belirgin özelliklerini sisteme girin.
                    </p>
                  </div>
                  <span className="rounded-full border border-[#1f3a68] bg-[#eef4ff] px-3 py-1 text-xs text-navy/80">
                    Tek komut, çoklu ajan mimarisi
                  </span>
                </div>

                <textarea
                  value={brief}
                  onChange={(event) => setBrief(event.target.value)}
                  placeholder={initialBrief}
                  className="min-h-[230px] w-full resize-none border-none bg-transparent px-6 py-6 font-sans text-[1rem] leading-8 text-stone-800 outline-none placeholder:text-stone-400"
                />

                <div className="border-t border-[#1f3a68] px-6 py-5">
                  <div>
                    <p className="text-[1.7rem] font-semibold tracking-[-0.035em] text-navy">Yönlendirme</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {refineOptions.map((item) => (
                        <button
                          key={item}
                          type="button"
                          onClick={() =>
                            setActiveRefineInstruction((current) =>
                              current === item ? "" : item,
                            )
                          }
                          className={`rounded-full border px-3.5 py-2 text-sm transition-all duration-200 ${
                            activeRefineInstruction === item
                              ? "border-[#1f3a68] bg-[#1f3a68] text-white"
                              : "border-[#1f3a68] bg-[#f2f6ff] text-navy"
                          }`}
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-4 border-t border-[#1f3a68] px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="max-w-xl space-y-1 text-sm leading-6 text-navy/75">
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
                      className="inline-flex items-center justify-center gap-2 rounded-full bg-[#1f3a68] px-5 py-3 text-sm font-medium text-white shadow-[0_8px_20px_rgba(31,58,104,0.18)] transition hover:bg-[#193257] hover:shadow-[0_10px_24px_rgba(31,58,104,0.24)] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <Search className="h-4 w-4" />
                      Araştır
                    </button>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <section className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-start lg:gap-10">
            <aside className="space-y-6">
              <div className="rounded-[32px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(244,248,255,0.5),rgba(255,255,255,0.88))] p-5 shadow-[0_16px_36px_rgba(31,58,104,0.07)] backdrop-blur-sm">
                <div className="mb-5 flex items-center justify-between border-b border-[#1f3a68] pb-4">
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
                <div className="rounded-[24px] border border-[#1f3a68] bg-[#fffaf7] p-5 text-sm leading-7 text-stone-700 shadow-[0_10px_28px_rgba(15,23,42,0.04)]">
                  <div className="flex items-center gap-3 text-navy">
                    <Sparkles className="h-4 w-4" />
                    <span className="font-medium">Sistem şu an sonuç üretemedi.</span>
                  </div>
                  <p className="mt-2">{errorMessage}</p>
                </div>
              ) : null}

              {result ? (
                <div className="space-y-6">
                  <section className="animate-soft-in rounded-[32px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(245,248,255,0.58),rgba(255,255,255,0.96))] p-6 shadow-[0_16px_34px_rgba(31,58,104,0.06)]">
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">
                        Profil Özeti
                      </p>
                      <span className="rounded-full border border-[#1f3a68] px-3 py-1 text-xs text-stone-500">
                        {result.profile_snapshot.inferred_persona}
                      </span>
                    </div>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div>
                        <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">
                          Öne Çıkan İlgi Alanları
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {result.profile_snapshot.obsessions.map((item) => (
                            <span
                              key={item}
                              className="rounded-full border border-[#1f3a68] bg-[#eef4ff] px-3 py-1 text-xs text-stone-600"
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">
                          İnce İpuçları
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {result.profile_snapshot.hidden_hooks.map((item) => (
                            <span
                              key={item}
                              className="rounded-full border border-[#1f3a68] bg-[#eef4ff] px-3 py-1 text-xs text-navy"
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
                <section className="rounded-[28px] border border-dashed border-[#1f3a68] bg-[linear-gradient(180deg,rgba(244,248,255,0.72),rgba(255,255,255,0.9))] p-7 shadow-[0_12px_28px_rgba(31,58,104,0.06)]">
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
