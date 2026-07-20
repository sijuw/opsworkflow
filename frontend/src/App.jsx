import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import EmailNotification from "./pages/EmailNotification";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/components/theme-provider";

function App() {
    return (
        <ThemeProvider defaultTheme="light" storageKey="sre-portal-theme">
            <Routes>
                <Route
                    path="/"
                    element={<Home />}
                />

                <Route
                    path="/email"
                    element={<EmailNotification />}
                />
            </Routes>

            <Toaster
                richColors
                position="top-right"
            />
        </ThemeProvider>
    );
}

export default App;