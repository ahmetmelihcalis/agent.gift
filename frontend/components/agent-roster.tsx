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
      <div className="rounded-[28px] border border-stone-300 bg-white/90 p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
        <p className="text-2xl font-semibold tracking-[-0.03em] text-navy">Ajanlar</p>
        <div className="mt-4 space-y-3">
          {agents.map((agent) => (
            <article
              key={agent.id}
              className="rounded-2xl border border-stone-300 bg-[linear-gradient(180deg,rgba(255,255,255,1),rgba(248,248,246,0.9))] px-4 py-4 transition-all duration-300 ease-out"
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
                        : "bg-stone-100 text-stone-500"
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
