"use client";

import { AgentState } from "@/lib/types";

type AgentRosterProps = {
  agents: AgentState[];
};

const statusLabel = {
  idle: "Beklemede",
  working: "İşleniyor",
  done: "Tamamlandı",
} as const;

const progressWidth = {
  idle: "14%",
  working: "56%",
  done: "100%",
} as const;

export function AgentRoster({ agents }: AgentRosterProps) {
  return (
    <section>
      <div className="rounded-[28px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(244,248,255,0.56),rgba(255,255,255,0.9))] p-5 shadow-[0_14px_32px_rgba(31,58,104,0.07)]">
        <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">Ajanlar</p>
        <div className="mt-4 space-y-3.5">
          {agents.map((agent) => (
            <article
              key={agent.id}
              className="rounded-[22px] border border-[#1f3a68] bg-[linear-gradient(180deg,rgba(236,244,255,0.88),rgba(255,255,255,0.98))] px-4 py-4 shadow-[0_8px_22px_rgba(15,23,42,0.03)] transition-all duration-300 ease-out"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-base font-semibold text-stone-900">{agent.name}</p>
                  <p className="mt-1 text-sm text-stone-500">{agent.role}</p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs ${
                    agent.status === "done"
                      ? "bg-emerald-50 text-emerald-700"
                      : agent.status === "working"
                        ? "bg-sky-50 text-sky-700"
                        : "bg-[#eef4ff] text-navy/70"
                  }`}
                >
                  {statusLabel[agent.status]}
                </span>
              </div>
              <div className="mt-4">
                <div className="relative h-2.5 overflow-hidden rounded-full bg-sky-100">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ease-out ${
                      agent.status === "done"
                        ? "bg-emerald-500"
                        : agent.status === "working"
                          ? "bg-sky-500"
                          : "bg-sky-200"
                    }`}
                    style={{ width: progressWidth[agent.status] }}
                  />
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
