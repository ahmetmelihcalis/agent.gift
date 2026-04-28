import { InvestigatePayload, StreamEvent } from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type ApiErrorPayload = {
  detail?: string | { msg?: string }[];
};

function parseSseBlock(block: string): StreamEvent | null {
  const normalizedBlock = block.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
  if (!normalizedBlock || normalizedBlock.startsWith(":")) {
    return null;
  }

  const lines = normalizedBlock.split("\n");
  const event = lines
    .find((line) => line.startsWith("event:"))
    ?.replace("event:", "")
    .trim();
  const dataLine = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.replace("data:", "").trim())
    .join("");

  if (!event || !dataLine) {
    return null;
  }

  return {
    event: event as StreamEvent["event"],
    data: JSON.parse(dataLine),
  } as StreamEvent;
}

export async function streamInvestigate(
  payload: InvestigatePayload,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/investigate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = "Sistem su an sonuc uretemedi.";

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (Array.isArray(payload.detail) && payload.detail[0]?.msg) {
        message = payload.detail[0].msg ?? message;
      }
    } catch {
      // Keep fallback message when the response is not JSON.
    }

    throw new Error(message);
  }

  if (!response.body) {
    throw new Error("Sunucudan akiş alinamadi.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const normalizedBuffer = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const blocks = normalizedBuffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const parsed = parseSseBlock(block);
      if (parsed) {
        onEvent(parsed);
      }
    }
  }

  const finalBlock = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
  if (finalBlock) {
    const parsed = parseSseBlock(finalBlock);
    if (parsed) {
      onEvent(parsed);
    }
  }
}
