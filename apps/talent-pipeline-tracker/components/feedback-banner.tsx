import type { FeedbackMessage } from "@/types/tracker";

export function FeedbackBanner({
  message,
}: {
  message: FeedbackMessage | null;
}) {
  if (!message) {
    return null;
  }

  const palette =
    message.type === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : "border-rose-200 bg-rose-50 text-rose-800";

  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${palette}`}>
      {message.text}
    </div>
  );
}
