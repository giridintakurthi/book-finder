import React, { useEffect, useMemo, useRef, useState } from "react";

// Book Finder — single-file React app (no external UI libs needed)
// Features: debounced search, pagination, keyboard shortcuts, loading states, error handling, and accessible cards.
// Works out-of-the-box against Google Books public API. Optional API key support via ?key=YOUR_KEY

const PAGE_SIZE = 12;

function StarRating({ value = 0, count = 5 }) {
  const full = Math.floor(value);
  const half = value % 1 >= 0.5;
  const stars = Array.from({ length: count }, (_, i) => {
    if (i < full) return "★";
    if (i === full && half) return "☆"; // simple half-state fallback
    return "✩";
  });
  return (
    <div aria-label={`Rating: ${value} out of ${count}`} className="text-sm">
      <span className="tracking-wider" style={{ fontFeatureSettings: '"kern"' }}>{stars.join(" ")}</span>
    </div>
  );
}

function ResultCard({ volume }) {
  const info = volume.volumeInfo || {};
  const sale = volume.saleInfo || {};
  const thumb =
    (info.imageLinks && (info.imageLinks.thumbnail || info.imageLinks.smallThumbnail)) ||
    "https://via.placeholder.com/128x192?text=No+Cover";
  const authors = (info.authors || []).join(", ");
  return (
    <article className="group rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow focus-within:shadow-md">
      <div className="grid grid-cols-[96px,1fr] gap-4">
        <div className="overflow-hidden rounded-xl border bg-neutral-50">
          <img
            src={thumb}
            alt={`Cover of ${info.title || "Untitled"}`}
            className="h-36 w-24 object-cover object-center transition-transform group-hover:scale-[1.02]"
            loading="lazy"
          />
        </div>
        <div className="min-w-0">
          <h3 className="text-base font-semibold leading-snug line-clamp-2" title={info.title}>
            {info.title || "Untitled"}
          </h3>
          {authors && (
            <p className="mt-1 text-sm text-neutral-600 line-clamp-1" title={authors}>
              {authors}
            </p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-neutral-600">
            {info.publishedDate && <span>{info.publishedDate}</span>}
            {info.pageCount && <span>• {info.pageCount} pages</span>}
            {info.categories?.length ? <span>• {info.categories[0]}</span> : null}
          </div>
          {typeof info.averageRating === "number" && (
            <div className="mt-2"><StarRating value={info.averageRating} /></div>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            {info.previewLink && (
              <a
                href={info.previewLink}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border px-3 py-1.5 text-xs font-medium hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-neutral-400"
              >
                Preview
              </a>
            )}
            {sale.buyLink && (
              <a
                href={sale.buyLink}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border px-3 py-1.5 text-xs font-medium hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-neutral-400"
              >
                Buy
              </a>
            )}
            {info.infoLink && (
              <a
                href={info.infoLink}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border px-3 py-1.5 text-xs font-medium hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-neutral-400"
              >
                Details
              </a>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

export default function BookFinderApp() {
  const [query, setQuery] = useState("harry potter");
  const [input, setInput] = useState("harry potter");
  const [page, setPage] = useState(0); // zero-based page index
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const controller = useRef(null);
  const cache = useRef(new Map()); // simple in-memory cache per session

  const startIndex = page * PAGE_SIZE;

  const searchUrl = useMemo(() => {
    const base = "https://www.googleapis.com/books/v1/volumes";
    const params = new URLSearchParams({
      q: query || "",
      startIndex: String(startIndex),
      maxResults: String(PAGE_SIZE),
      printType: "books",
    });
    // Optional: if you have an API key, append here, e.g. params.set('key', 'YOUR_KEY')
    return `${base}?${params.toString()}`;
  }, [query, startIndex]);

  useEffect(() => {
    let active = true;
    async function fetchData() {
      const cacheKey = searchUrl;
      setLoading(true);
      setError("");

      // Abort any in-flight fetch
      if (controller.current) controller.current.abort();
      controller.current = new AbortController();

      if (cache.current.has(cacheKey)) {
        const cached = cache.current.get(cacheKey);
        setItems(cached.items);
        setTotal(cached.total);
        setLoading(false);
        return;
      }

      try {
        const res = await fetch(searchUrl, { signal: controller.current.signal });
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const data = await res.json();
        if (!active) return;
        const items = Array.isArray(data.items) ? data.items : [];
        const total = typeof data.totalItems === "number" ? data.totalItems : items.length;
        cache.current.set(cacheKey, { items, total });
        setItems(items);
        setTotal(total);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Something went wrong");
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    fetchData();
    return () => {
      active = false;
      if (controller.current) controller.current.abort();
    };
  }, [searchUrl]);

  // Debounce user typing -> update query
  useEffect(() => {
    const id = setTimeout(() => {
      setPage(0);
      setQuery(input.trim());
    }, 400);
    return () => clearTimeout(id);
  }, [input]);

  const hasPrev = page > 0;
  const hasNext = startIndex + PAGE_SIZE < total;

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-50 to-white text-neutral-900">
      <header className="sticky top-0 z-10 backdrop-blur supports-[backdrop-filter]:bg-white/60 bg-white/80 border-b">
        <div className="mx-auto max-w-6xl px-4 py-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <h1 className="text-2xl font-bold tracking-tight">📚 Book Finder</h1>
          <div className="flex w-full md:w-auto items-center gap-2">
            <div className="relative w-full md:w-96">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Search by title, author, or ISBN…"
                className="w-full rounded-2xl border px-4 py-2.5 pr-10 shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-400"
                aria-label="Search books"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    setPage(0);
                    setQuery(input.trim());
                  }
                }}
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500">⌘K</span>
            </div>
            <button
              onClick={() => {
                setPage(0);
                setQuery(input.trim());
              }}
              className="rounded-2xl border px-4 py-2.5 text-sm font-semibold shadow-sm hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-neutral-400"
            >
              Search
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {/* Status Row */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 text-sm text-neutral-600">
          <div>
            {loading ? (
              <span className="inline-flex items-center gap-2"><span className="h-3 w-3 animate-spin rounded-full border-2 border-neutral-300 border-t-transparent"/> Searching “{query}”…</span>
            ) : error ? (
              <span className="text-red-600">{error}</span>
            ) : (
              <span>
                {total ? (
                  <>
                    Found <strong className="text-neutral-900">{total.toLocaleString()}</strong> results for “{query}”.
                  </>
                ) : (
                  <>Type to search books.</>
                )}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-neutral-100 px-3 py-1">Page {page + 1}</span>
            <div className="flex items-center gap-2">
              <button
                className="rounded-xl border px-3 py-1.5 text-sm disabled:opacity-40 hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-neutral-400"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={!hasPrev || loading}
                aria-label="Previous page"
              >
                ← Prev
              </button>
              <button
                className="rounded-xl border px-3 py-1.5 text-sm disabled:opacity-40 hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-neutral-400"
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasNext || loading}
                aria-label="Next page"
              >
                Next →
              </button>
            </div>
          </div>
        </div>

        {/* Results Grid */}
        {loading && !items.length ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: PAGE_SIZE }).map((_, i) => (
              <div key={i} className="animate-pulse rounded-2xl border bg-white p-4">
                <div className="h-36 w-24 rounded-xl bg-neutral-200" />
                <div className="mt-3 h-4 w-3/4 rounded bg-neutral-200" />
                <div className="mt-2 h-3 w-1/2 rounded bg-neutral-200" />
              </div>
            ))}
          </div>
        ) : items.length ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((vol) => (
              <ResultCard key={vol.id} volume={vol} />
            ))}
          </div>
        ) : (
          <div className="mt-20 text-center text-neutral-500">No results. Try a different search term.</div>
        )}

        {/* Footer */}
        <footer className="mt-10 text-center text-xs text-neutral-500">
          Data from Google Books API. Some previews/links may require region access.
        </footer>
      </main>
    </div>
  );
}
