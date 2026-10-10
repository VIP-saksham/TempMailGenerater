/**
 * cloudflare email worker
 *
 * apne domain pe aane wali harka mail forwards karega tumhare VPS pe.
 *
 * setup:
 *  1. apna domain Cloudflare pe add karo
 *  2. Email → Email Routing → enable karo
 *  3. Catch-all rule → Action: Send to Worker → ye worker选择 karo
 *  4. APP_URL me tumhara VPS/host domain daalo, INGEST_KEY = .env wali value
 */

const APP_URL = "https://mail.yourdomain.com";
const INGEST_KEY = "change-me-to-long-random";

export default {
  async email(message, env, ctx) {
    const raw = new Response(message.raw);
    const buf = await raw.arrayBuffer();

    try {
      const res = await fetch(`${APP_URL}/mail/ingest/raw`, {
        method: "POST",
        headers: {
          "content-type": "message/rfc822",
          "x-ingest-key": INGEST_KEY,
        },
        body: buf,
      });
      if (!res.ok) {
        console.error("ingest failed", res.status, await res.text());
      }
    } catch (e) {
      console.error("ingest error", e);
    }
  },
};
