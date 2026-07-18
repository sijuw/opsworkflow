import EmailForm from "../components/EmailForm";

function Home() {
  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <EmailForm />
      </div>
    </div>
  );
}

export default Home;