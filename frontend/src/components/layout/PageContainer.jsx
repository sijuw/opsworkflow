import { ModeToggle } from "@/components/ModeToggle"; 

export default function PageContainer({ children, maxWidth = "2xl" }) {
  const maxWidthClass = {
    "2xl": "max-w-2xl",
    "3xl": "max-w-3xl",
    "4xl": "max-w-4xl",
    "5xl": "max-w-5xl",
    "6xl": "max-w-6xl",
    "7xl": "max-w-7xl",
  }[maxWidth] || "max-w-2xl";

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-950 transition-colors duration-300">
      <div className={`mx-auto px-6 py-10 ${maxWidthClass}`}>
        
        {/* Flex container to push the button perfectly to the right */}
        <div className="mb-6 flex w-full justify-end">
          <ModeToggle />
        </div>

        {children}
      </div>
    </div>
  );
}