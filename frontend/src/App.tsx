import { useEffect, useState } from "react";

import { apiUrl } from "./lib/apiBase";

type HelloResponse = { message: string; service: string; project?: string };

export function App() {
  const [data, setData] = useState<HelloResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(apiUrl("/api/hello"));
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          const msg =
            typeof body === "object" &&
            body !== null &&
            "error" in body &&
            typeof (body as { error?: { message?: string } }).error?.message === "string"
              ? (body as { error: { message: string } }).error.message
              : res.statusText;
          throw new Error(msg);
        }
        const json = (await res.json()) as HelloResponse;
        if (!cancelled) {
          setData(json);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Request failed");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        margin: 0,
        fontFamily: "system-ui, sans-serif",
        background: "#18181b",
        color: "#e4e4e7",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "1rem",
        padding: "2rem",
      }}
    >
      <h1 style={{ fontSize: "1.75rem", fontWeight: 600 }}>
        Meridian Stores
        {data?.project !== undefined ? (
          <span style={{ color: "#a1a1aa", fontWeight: 400 }}> ({data.project})</span>
        ) : null}
      </h1>
      {error !== null ? (
        <p style={{ color: "#f87171" }} role="alert">
          {error}
        </p>
      ) : data === null ? (
        <p style={{ color: "#a1a1aa" }}>Loading…</p>
      ) : (
        <>
          <p style={{ fontSize: "1.125rem" }}>{data.message}</p>
          <p style={{ color: "#a1a1aa", fontSize: "0.875rem" }}>service: {data.service}</p>
        </>
      )}
      <p style={{ color: "#71717a", fontSize: "0.75rem", maxWidth: "32rem", textAlign: "center" }}>
        Set <code>PROJECT_NAME</code> in <code>meridian-stores/config/.env</code> to rename the deployment;
        optional <code>MERIDIAN_STORES_*</code> overrides. Dev server: <code>meridian-stores/frontend/.env</code>{" "}
        (<code>VITE_*</code>).
      </p>
    </main>
  );
}
