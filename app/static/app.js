const $ = id => document.getElementById(id);
let currentInbox = null;
let pollTimer = null;

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "request failed");
  }
  return res.json();
}

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 2200);
}

async function newInbox() {
  const localPart = $("localPart").value.trim();
  const body = localPart ? { local_part: localPart } : {};
  try {
    const inbox = await api("/mail/inbox", { method: "POST", body: JSON.stringify(body) });
    currentInbox = inbox;
    $("addrText").textContent = inbox.address;
    $("addrBox").classList.remove("hidden");
    $("messages").classList.remove("hidden");
    $("localPart").value = "";
    await loadMessages();
    startPolling();
    toast("Inbox ready!");
  } catch (e) {
    toast(e.message);
  }
}

async function loadMessages() {
  if (!currentInbox) return;
  try {
    const msgs = await api(`/mail/inbox/${currentInbox.id}/messages`);
    render(msgs);
  } catch (e) {
    if (String(e.message).includes("404")) {
      currentInbox = null;
      $("addrBox").classList.add("hidden");
      $("messages").classList.add("hidden");
      stopPolling();
      toast("Inbox expired");
    }
  }
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s || "";
  return d.innerHTML;
}

function render(msgs) {
  const list = $("msgList");
  if (!msgs.length) {
    list.innerHTML = '<p class="empty">No messages yet. Send a mail to your address — it\'ll show up in a few seconds.</p>';
    return;
  }
  list.innerHTML = msgs.map(m => `
    <div class="msg-item">
      <div class="msg-head">
        <span class="msg-sender">${esc(m.sender)}</span>
        <span class="msg-time">${new Date(m.received_at).toLocaleString()}</span>
      </div>
      <div class="msg-subject">${esc(m.subject) || "(no subject)"}${m.otp ? `<span class="otp-tag">OTP: ${esc(m.otp)}</span>` : ""}</div>
      <div class="msg-body">${esc((m.body_text || "").slice(0, 500))}</div>
    </div>
  `).join("");
}

async function delInbox() {
  if (!currentInbox) return;
  if (!confirm("Delete this inbox and all its messages?")) return;
  try {
    await api(`/mail/inbox/${currentInbox.id}`, { method: "DELETE" });
    currentInbox = null;
    $("addrBox").classList.add("hidden");
    $("messages").classList.add("hidden");
    stopPolling();
    toast("Inbox deleted");
  } catch (e) {
    toast(e.message);
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(loadMessages, 5000);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

$("newInbox").addEventListener("click", newInbox);
$("localPart").addEventListener("keydown", e => { if (e.key === "Enter") newInbox(); });
$("delInbox").addEventListener("click", delInbox);
$("refresh").addEventListener("click", loadMessages);

$("copyAddr").addEventListener("click", () => {
  if (!currentInbox) return;
  navigator.clipboard.writeText(currentInbox.address).then(() => toast("Copied!"));
});

window.addEventListener("beforeunload", stopPolling);
