export function ErrorState({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-[1.75rem] border border-rose-200 bg-rose-50 px-6 py-8">
      <h3 className="text-lg font-semibold text-rose-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-rose-700">{message}</p>
      {onRetry ? (
        <button
          className="mt-4 rounded-full bg-rose-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-700"
          onClick={onRetry}
          type="button"
        >
          Reintentar
        </button>
      ) : null}
    </div>
  );
}
