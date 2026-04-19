export default function Loading() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f4f8f5_0%,#edf4ef_48%,#e5ece7_100%)] px-6 py-14">
      <div className="mx-auto max-w-6xl animate-pulse space-y-6">
        <div className="h-12 w-64 rounded-full bg-white/70" />
        <div className="grid gap-4 md:grid-cols-3">
          <div className="h-24 rounded-3xl bg-white/70" />
          <div className="h-24 rounded-3xl bg-white/70" />
          <div className="h-24 rounded-3xl bg-white/70" />
        </div>
        <div className="h-[28rem] rounded-[2rem] bg-white/70" />
      </div>
    </main>
  );
}
