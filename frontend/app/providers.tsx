"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { Toaster } from "react-hot-toast";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#1c1c1e",
            color: "rgba(255,255,255,0.7)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: "12px",
            fontFamily: "var(--font-mono)",
            fontSize: "13px",
          },
        }}
      />
    </QueryClientProvider>
  );
}
