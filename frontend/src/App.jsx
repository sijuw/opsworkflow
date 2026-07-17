import Home from "./pages/Home";
// Import the Toaster from your ui folder
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <>
      <Home />
      {/* Add the Toaster here. richColors makes the success/error toasts green and red */}
      <Toaster richColors position="top-right" />
    </>
  );
}

export default App;