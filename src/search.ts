import { Readability } from "jsr:@paoramen/cheer-reader";
import * as cheerio from "npm:cheerio@1.0.0";

// HTML cleaning function
const htmlToText = (html: string) => {
  const $ = cheerio.load(html);
  const parsed = new Readability($).parse();
  return parsed?.textContent?.replace(/\s+/g, " ").trim() || "";
};

// Get search URL from environment variables or use default
const SEARCH_URL = Deno.env.get("SEARCH_URL") || "http://localhost:3001/"; // Updated instance

async function handleRequest(request: Request): Promise<Response> {
  try {
    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { "Content-Type": "application/json" },
      });
    }

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response(
        JSON.stringify({ success: false, error: "Invalid JSON format" }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    if (!body.query) {
      return new Response(
        JSON.stringify({ success: false, error: "Query parameter is required" }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    const searchEndpoint = new URL("/search", SEARCH_URL);
    searchEndpoint.searchParams.set("q", body.query);
    searchEndpoint.searchParams.set("format", "json");

    console.log("Search URL:", searchEndpoint.toString());

    const searchRes = await fetch(searchEndpoint, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
      },
    });

    console.log("Search response status:", searchRes.status);

    if (!searchRes.ok) {
      const errorText = await searchRes.text();
      console.error("Search response error:", errorText);
      throw new Error(`Search request failed with status ${searchRes.status}`);
    }

    const { results } = await searchRes.json();
    if (!Array.isArray(results)) {
      return new Response(
        JSON.stringify({ success: false, error: "Invalid search results format" }),
        { status: 500, headers: { "Content-Type": "application/json" } },
      );
    }


    const contexts = [];
    let index = 0;
    while (contexts.length < 3 && index < results.length) {
      const result = results[index];
      index++;
      try {
        const response = await fetch(result.url);
        if (!response.ok) {
          console.warn(`Skipping ${result.url} due to non-ok response`);
          continue;
        }
        const html = await response.text();
        contexts.push({
          url: result.url,
          content: htmlToText(html),
        });
      } catch (error) {
        console.error(`Failed to process ${result.url}:`, error);
      }
    }

    return new Response(
      JSON.stringify({ success: true, data: contexts }),
      { headers: { "Content-Type": "application/json" } },
    );

  } catch (error) {
    console.error("Processing error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Processing failed",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
}

// Start server
Deno.serve({ port: 8000 }, (req) => handleRequest(req));
