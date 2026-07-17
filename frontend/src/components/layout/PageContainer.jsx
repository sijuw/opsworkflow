export default function PageContainer({ children }) {
  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto max-w-5xl px-6 py-10">
        {children}
      </div>
    </div>
  );
}