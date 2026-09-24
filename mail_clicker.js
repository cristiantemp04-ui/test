#!/usr/bin/env node
/**
 * mail_clicker.js
 * -----------------------------------------------------------------------------
 * Piccolo tool di automazione UI: apre la webmail, clicca il pulsante di
 * refresh (il cerchio / freccia circolare in alto) e poi apre la prima mail
 * della lista (quella più in alto = l'ultima arrivata).
 *
 * Non fa login "magico": per stare dentro il tuo account usa un file di
 * storage state (cookie/sessione) che generi una volta con `--login`.
 *
 * Uso:
 *   # 1) La prima volta, fai login a mano e salva la sessione:
 *   node mail_clicker.js --login --url "https://tua-webmail.example"
 *
 *   # 2) Poi lancia l'automazione (refresh + apri ultima mail):
 *   node mail_clicker.js --url "https://tua-webmail.example"
 *
 * Opzioni principali (anche via variabili d'ambiente):
 *   --url <URL>                pagina della inbox            (env URL)
 *   --refresh <selettore>      selettore del pulsante refresh(env REFRESH_SELECTOR)
 *   --email <selettore>        selettore della riga mail     (env EMAIL_SELECTOR)
 *   --storage <file>           file sessione                 (default: ./mail_state.json)
 *   --login                    apre il browser per fare login e salva la sessione
 *   --headed                   mostra la finestra del browser
 *   --wait <ms>                attesa dopo il refresh        (default 1500)
 *   --keep-open                lascia il browser aperto a fine run
 * -----------------------------------------------------------------------------
 */

// Playwright è installato globalmente in questo ambiente: risolvilo da lì se
// non è tra le dipendenze locali.
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch {
  ({ chromium } = require("/opt/node22/lib/node_modules/playwright"));
}
const fs = require("fs");

// ---------- parsing argomenti -------------------------------------------------
function parseArgs(argv) {
  const a = { flags: new Set(), opt: {} };
  for (let i = 2; i < argv.length; i++) {
    const t = argv[i];
    if (t === "--login") a.flags.add("login");
    else if (t === "--headed") a.flags.add("headed");
    else if (t === "--keep-open") a.flags.add("keepOpen");
    else if (t.startsWith("--")) a.opt[t.slice(2)] = argv[++i];
  }
  return a;
}
const args = parseArgs(process.argv);

const CONFIG = {
  url: args.opt.url || process.env.URL || "",
  storage: args.opt.storage || process.env.STORAGE || "./mail_state.json",
  waitAfterRefresh: Number(args.opt.wait || process.env.WAIT || 1500),
  headed: args.flags.has("headed") || args.flags.has("login"),

  // Selettore del pulsante di refresh. Sovrascrivi con --refresh se le
  // euristiche non lo trovano. Il default prova le forme più comuni per
  // un'icona "freccia circolare" / cerchio.
  refresh:
    args.opt.refresh ||
    process.env.REFRESH_SELECTOR ||
    [
      'button[aria-label*="refresh" i]',
      'button[title*="refresh" i]',
      '[aria-label*="aggiorna" i]',
      '[title*="aggiorna" i]',
      '[data-testid*="refresh" i]',
      'button:has(svg[class*="refresh" i])',
      'button:has(.icon-refresh)',
    ].join(", "),

  // Selettore della riga mail da aprire. Il default prende il PRIMO elemento
  // della lista (la mail più recente sta in cima).
  email:
    args.opt.email ||
    process.env.EMAIL_SELECTOR ||
    [
      '[role="listbox"] [role="option"]',
      '[role="list"] [role="listitem"]',
      '[data-testid*="message" i]',
      '[class*="mail-item" i]',
      '[class*="email-item" i]',
      "ul li a",
      "li[tabindex]",
    ].join(", "),
};

// ---------- helper: primo selettore che trova qualcosa ------------------------
async function firstVisible(page, selectorList, { timeout = 8000 } = {}) {
  const parts = selectorList.split(",").map((s) => s.trim()).filter(Boolean);
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    for (const sel of parts) {
      const loc = page.locator(sel).first();
      if ((await loc.count()) && (await loc.isVisible().catch(() => false))) {
        return loc;
      }
    }
    await page.waitForTimeout(200);
  }
  return null;
}

async function main() {
  if (!CONFIG.url) {
    console.error("[!] Manca l'URL. Usa --url \"https://tua-webmail\" (o env URL).");
    process.exit(2);
  }

  const browser = await chromium.launch({
    headless: !CONFIG.headed,
    executablePath: process.env.PW_CHROMIUM || undefined,
  });

  const hasState = fs.existsSync(CONFIG.storage);
  const context = await browser.newContext(
    hasState ? { storageState: CONFIG.storage } : {}
  );
  const page = await context.newPage();

  console.log(`[*] Apro ${CONFIG.url}`);
  await page.goto(CONFIG.url, { waitUntil: "domcontentloaded" });

  // --- modalità login: aspetti che l'utente entri, poi salvi la sessione -----
  if (args.flags.has("login")) {
    console.log("[*] Fai il login nella finestra del browser.");
    console.log("    Quando sei dentro la inbox, premi INVIO qui per salvare la sessione...");
    await new Promise((r) => process.stdin.once("data", r));
    await context.storageState({ path: CONFIG.storage });
    console.log(`[+] Sessione salvata in ${CONFIG.storage}`);
    await browser.close();
    process.exit(0);
  }

  // --- 1) click sul cerchio / refresh ----------------------------------------
  const refreshBtn = await firstVisible(page, CONFIG.refresh);
  if (!refreshBtn) {
    console.error(
      "[!] Pulsante refresh non trovato. Passa il selettore giusto con --refresh \"...\"."
    );
    if (!args.flags.has("keepOpen")) await browser.close();
    process.exit(1);
  }
  await refreshBtn.click();
  console.log("[+] Refresh cliccato.");

  // attende il ricaricamento della lista
  await page.waitForTimeout(CONFIG.waitAfterRefresh);
  await page.waitForLoadState("networkidle").catch(() => {});

  // --- 2) click sulla prima mail (la più recente) ----------------------------
  const firstMail = await firstVisible(page, CONFIG.email);
  if (!firstMail) {
    console.error(
      "[!] Nessuna mail trovata nella lista. Passa il selettore con --email \"...\"."
    );
    if (!args.flags.has("keepOpen")) await browser.close();
    process.exit(1);
  }

  const subject = (await firstMail.innerText().catch(() => "")).split("\n")[0];
  await firstMail.click();
  console.log(`[+] Aperta l'ultima mail: ${subject || "(oggetto non leggibile)"}`);

  if (args.flags.has("keepOpen")) {
    console.log("[*] --keep-open attivo: chiudi il browser a mano quando hai finito.");
  } else {
    await page.waitForTimeout(500);
    await browser.close();
  }
}

main().catch((err) => {
  console.error("[x] Errore:", err.message);
  process.exit(1);
});
