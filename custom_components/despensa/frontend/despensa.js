/*
 * Despensa – inventario de casa para Home Assistant, enlazado con Cesta.
 * Define <despensa-panel> (panel de la barra lateral) y <despensa-card> (tarjeta).
 * Sin dependencias: un único módulo que sirve la integración.
 */
const DESPENSA_VERSION = "1.0.0";

/* ------------------------------------------------------------ utilidades */
const P = {
  menu: "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z",
  cog: "M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",
  close: "M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",
  search: "M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z",
  plus: "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",
  minus: "M19,13H5V11H19V13Z",
  check: "M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z",
  cartPlus: "M11 9H13V6H16V4H13V1H11V4H8V6H11M7 18C5.9 18 5 18.9 5 20S5.9 22 7 22 9 21.1 9 20 8.1 18 7 18M17 18C15.9 18 15 18.9 15 20S15.9 22 17 22 19 21.1 19 20 18.1 18 17 18M7.2 14.8V14.7L8.1 13H15.5C16.2 13 16.9 12.6 17.2 12L21.1 5L19.4 4L15.5 11H8.5L4.3 2H1V4H3L6.6 11.6L5.2 14C5.1 14.3 5 14.6 5 15C5 16.1 5.9 17 7 17H19V15H7.4C7.3 15 7.2 14.9 7.2 14.8Z",
  cartCheck: "M9 20C9 21.1 8.1 22 7 22S5 21.1 5 20 5.9 18 7 18 9 18.9 9 20M17 18C15.9 18 15 18.9 15 20S15.9 22 17 22 19 21.1 19 20 18.1 18 17 18M7.2 14.8V14.7L8.1 13H15.5C16.2 13 16.9 12.6 17.2 12L21.1 5L19.4 4L15.5 11H8.5L4.3 2H1V4H3L6.6 11.6L5.2 14C5.1 14.3 5 14.6 5 15C5 16.1 5.9 17 7 17H19V15H7.4C7.3 15 7.2 14.9 7.2 14.8M18 2.8L16.6 1.4L11.8 6.2L9.2 3.6L7.8 5L11.8 9L18 2.8Z",
  mic: "M17.3,11C17.3,14 14.76,16.1 12,16.1C9.24,16.1 6.7,14 6.7,11H5C5,14.41 7.72,17.23 11,17.72V21H13V17.72C16.28,17.23 19,14.41 19,11M10.8,4.9C10.8,4.24 11.34,3.7 12,3.7C12.66,3.7 13.2,4.24 13.2,4.9L13.19,11.1C13.19,11.76 12.66,12.3 12,12.3C11.34,12.3 10.8,11.76 10.8,11.1M12,14A3,3 0 0,0 15,11V5A3,3 0 0,0 12,2A3,3 0 0,0 9,5V11A3,3 0 0,0 12,14Z",
  chevron: "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",
};
const svg = (p, s = 24) =>
  `<svg viewBox="0 0 24 24" width="${s}" height="${s}" aria-hidden="true" focusable="false"><path d="${p}" fill="currentColor"/></svg>`;

const norm = (s) =>
  String(s ?? "").normalize("NFKD").replace(/[̀-ͯ]/g, "").trim().toLowerCase().replace(/\s+/g, " ");
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const cap = (s) => {
  s = String(s ?? "").replace(/\s+/g, " ").trim();
  return s ? s[0].toUpperCase() + s.slice(1) : s;
};
const rgb = (hex) => {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || "");
  const n = parseInt(m ? m[1] : "78909c", 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const onColor = (hex) => {
  const [r, g, b] = rgb(hex).map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.45 ? "#1d1b16" : "#ffffff";
};
/* Variables CSS de color de una balda (mismas que Cesta) */
const tone = (hex) => {
  const [r, g, b] = rgb(hex);
  return `--c:${hex};--on-c:${onColor(hex)};--c1:rgba(${r},${g},${b},.15);--c2:rgba(${r},${g},${b},.34);--c3:rgba(${r},${g},${b},.7)`;
};
const nowS = () => Date.now() / 1000;
const ago = (ts) => {
  const s = nowS() - ts;
  if (s < 60) return "ahora";
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  const d = Math.floor(s / 86400);
  if (d === 1) return "ayer";
  if (d < 30) return `hace ${d} días`;
  const m = Math.floor(d / 30);
  return m === 1 ? "hace 1 mes" : `hace ${m} meses`;
};
const stem = (w) => {
  if (w.length > 3 && w.endsWith("s")) w = w.slice(0, -1);
  if (w.length > 3 && w.endsWith("e")) w = w.slice(0, -1);
  return w;
};
const stems = (t) => norm(t).split(/[^a-z0-9]+/).filter(Boolean).map(stem);
const byName = (a, b) => a.name.localeCompare(b.name, "es", { sensitivity: "base" });
/* "bricks" con 1 → "brick"; "unidades" → "unidad" */
const unitFor = (unit, n) => {
  unit = String(unit || "").trim();
  if (n !== 1 || unit.length < 3 || !unit.endsWith("s")) return unit;
  if (/[dlnzj]es$/.test(unit) && unit.length > 4) return unit.slice(0, -2);
  return unit.slice(0, -1);
};
/* Guiones suaves en palabras largas ("Man·te·qui·lla") para que no se partan en cualquier letra */
const soft = (s) =>
  esc(s).replace(/[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{9,}/g, (w) =>
    w.replace(/([aeiouáéíóúü])(?=(?:ch|ll|rr|[bcdfghjklmnñpqrstvwxyz])[aeiouáéíóúü])/gi, "$1\u00AD")
  );
const qty = (n, unit) => (unit ? `${n} ${unitFor(unit, n)}` : String(n));
const isLow = (it) => it.min_stock !== null && it.min_stock !== undefined && it.stock <= it.min_stock;
const MINUS = "−";
const KIND = { used: "Usado", empty: "Se acabó", purchased: "Comprado en la Cesta", added: "Añadido", set: "Corregido" };
const SOURCE = { voz: " por voz", accion: " por una automatización", panel: "", cesta: "" };
const UNITS = ["uds", "bricks", "latas", "botes", "paquetes", "botellas", "bolsas", "rollos", "tarros", "cajas", "kg"];

const EXTRA_EMOJI = "🍏🥗🍳🥘🍲🫕🥙🌯🍔🍕🌭🥪🍿🧃🧋🍶🍵🥤🧉🍾🧊🧂🫙🥫🍯🧈🥜🌰🫘🌾🍚🍝🍜🥟🍤🍣🍱🧆🥨🥯🥞🧇🥐🍩🍪🎂🍰🧁🥧🍫🍬🍭🍮🍦🍧🍨🧀🥚🥓🥩🍗🍖🦴🐟🦐🦑🦀🐙🦪🧻🧼🧽🧴🪥🪒🧹🧺🪣🧯🧤🔋💡🕯️📦🗑️💊🩹🌸💐🪴🎁🐶🐱🐾🐠👶🍼💄🧦🎈🖊️📰🔥🛒🏪";

/* -------------------------------------------------------------- estilos */
const STYLE = `
:host{display:block;color:var(--primary-text-color,#1c1b1f);font-family:var(--ha-font-family-body,var(--paper-font-body1_-_font-family,Roboto,system-ui,-apple-system,"Segoe UI",sans-serif));-webkit-tap-highlight-color:transparent;
  --wood-base:var(--despensa-wood,#9b6430);
  --surface:var(--card-background-color,#fff);
  --wood:color-mix(in srgb,var(--wood-base) 50%,var(--surface));
  --wood-dark:color-mix(in srgb,var(--wood-base) 68%,var(--surface));
  --wood-light:color-mix(in srgb,var(--wood-base) 30%,var(--surface));
  --back:color-mix(in srgb,var(--wood-base) 7%,var(--primary-background-color,#f4f5f2));
  --low:var(--warning-color,#f5a400);
  --out:var(--error-color,#db4437);
  --plus:var(--success-color,#2e7d32)}
:host([mode=panel]){height:100%}
*{box-sizing:border-box}
[hidden]{display:none!important}
button{font:inherit;color:inherit}
.app{position:relative;display:flex;flex-direction:column;height:100%;container-type:inline-size}
:host([mode=panel]) .app{background:var(--primary-background-color,#f4f5f2)}
.em,.emoji{font-family:"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif;font-style:normal}

/* barra superior */
.toolbar{flex:none;display:flex;align-items:center;gap:2px;height:var(--header-height,56px);padding:0 4px;background:var(--app-header-background-color,var(--primary-background-color));color:var(--app-header-text-color,var(--primary-text-color));border-bottom:var(--app-header-border-bottom,none)}
.toolbar h1{flex:1;margin:0 0 0 12px;font-size:20px;font-weight:400;display:flex;align-items:baseline;gap:10px;white-space:nowrap;overflow:hidden}
.toolbar h1 small{font-size:14px;opacity:.72}
:host([mode=card]) .toolbar{height:auto;padding:12px 8px 0 16px;background:none;color:inherit;border:0}
:host([mode=card]) .toolbar h1{margin:0;font-size:var(--ha-card-header-font-size,22px)}
.icon-btn{display:grid;place-items:center;width:40px;height:40px;border-radius:50%;border:0;background:none;cursor:pointer;flex:none}
.icon-btn:hover{background:rgba(127,127,127,.12)}
.icon-btn:focus-visible,.chip:focus-visible,.tile:focus-visible,.text-btn:focus-visible,.btn:focus-visible,.move:focus-visible,.round:focus-visible,summary:focus-visible,.switch input:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}

.scroller{flex:1;overflow-y:auto;overscroll-behavior:contain}
:host([mode=card]) .scroller{overflow:visible}
.layout{width:100%;max-width:1240px;margin:0 auto;padding:4px 16px 96px;display:grid;grid-template-columns:minmax(0,1fr);gap:28px}
:host([mode=card]) .layout{padding:4px 16px 16px}
@container (min-width:860px){
  .layout{grid-template-columns:minmax(0,1fr) minmax(280px,340px);gap:32px;padding:8px 28px 96px}
  .side{padding-top:12px}
  :host([mode=panel]) .side{position:sticky;top:0;align-self:start;max-height:calc(100vh - var(--header-height,56px));overflow:auto;padding-bottom:24px;scrollbar-width:thin}
}

/* buscador */
.addwrap{padding:10px 0 2px}
:host([mode=panel]) .addwrap{position:sticky;top:0;z-index:3;background:var(--primary-background-color,#f4f5f2)}
.addbar{display:flex;align-items:center;gap:6px;height:48px;padding:0 4px 0 14px;border-radius:24px;background:var(--surface);border:1px solid var(--divider-color,rgba(0,0,0,.12));color:var(--secondary-text-color)}
.addbar:focus-within{border-color:var(--primary-color,#03a9f4);box-shadow:inset 0 0 0 1px var(--primary-color,#03a9f4)}
.addbar input{flex:1;min-width:0;height:100%;border:0;background:none;outline:none;font:inherit;font-size:16px;color:var(--primary-text-color)}
.addbar input::placeholder{color:var(--secondary-text-color);opacity:.9}
.results{margin-top:12px}
.hint{margin:8px 2px 0;font-size:12.5px;color:var(--secondary-text-color)}

/* filtros */
.filters{display:flex;gap:8px;overflow-x:auto;padding:12px 0 2px;scrollbar-width:none}
.filters::-webkit-scrollbar{display:none}
.chip{flex:none;display:inline-flex;align-items:center;gap:6px;height:34px;padding:0 14px;border-radius:17px;border:1px solid var(--divider-color,rgba(0,0,0,.14));background:var(--surface);cursor:pointer;font-size:14px;white-space:nowrap}
.chip .n{opacity:.66;font-variant-numeric:tabular-nums}
.chip[aria-pressed=true]{background:var(--primary-color,#03a9f4);border-color:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff)}
.chip.dept[aria-pressed=true]{background:var(--c1);border-color:var(--c);color:inherit;box-shadow:inset 0 0 0 1px var(--c)}
.chip .dot{width:10px;height:10px;border-radius:50%;background:var(--c)}
.chip .bang{display:grid;place-items:center;width:18px;height:18px;border-radius:50%;background:var(--low);color:#1d1b16;font-size:12px;font-weight:800}
.chip svg{flex:none}

/* el armario */
.cupboard{position:relative;margin-top:16px;padding:6px 12px 10px;border:12px solid var(--wood);border-top-width:16px;border-radius:16px 16px 10px 10px;background:var(--back);
  box-shadow:inset 0 1px 0 var(--wood-dark),inset 0 14px 22px -16px rgba(0,0,0,.45),0 1px 0 var(--wood-dark),0 10px 24px -14px rgba(60,35,15,.45)}
.cupboard::after{content:"";position:absolute;left:18%;right:18%;bottom:-22px;height:10px;border-radius:0 0 6px 6px;background:var(--wood-dark)}
.shelf{position:relative;padding-top:18px}
.shelf+.shelf{margin-top:16px}
.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:8px;align-items:end;padding:0 4px}
.plank{position:relative;height:13px;margin:0 -12px;background:linear-gradient(var(--wood-light) 0 3px,var(--wood) 3px 10px,var(--wood-dark) 10px);box-shadow:0 7px 10px -6px rgba(40,20,5,.4)}
.label{position:absolute;left:18px;top:7px;display:inline-flex;align-items:center;gap:7px;max-width:calc(100% - 36px);height:24px;padding:0 10px 0 8px;border-radius:0 0 8px 8px;background:var(--surface);border:1px solid var(--c2);border-top:3px solid var(--c);font-size:12.5px;font-weight:500;white-space:nowrap;box-shadow:0 2px 4px rgba(0,0,0,.12)}
.label .ico{font-size:13px}
.label .txt{overflow:hidden;text-overflow:ellipsis}
.label .n{color:var(--secondary-text-color);font-weight:400;font-variant-numeric:tabular-nums}

/* productos */
.tile{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;min-height:104px;padding:14px 6px 9px;border-radius:16px 16px 6px 6px;border:1px solid var(--c2);border-bottom-width:2px;background:var(--c1);text-align:center;cursor:pointer;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none;touch-action:manipulation;transition:transform .14s ease}
.tile:active{transform:scale(.95)}
.cupboard .tile{background:color-mix(in srgb,var(--c) 15%,var(--surface))}
.tile .em{font-size:32px;line-height:1.05}
.tile .nm{font-size:13px;font-weight:500;line-height:1.22;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere;hyphens:manual}
.tile .qty{max-width:100%;font-size:12px;line-height:1.2;color:var(--secondary-text-color);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-variant-numeric:tabular-nums}
.tile .qty b{font-size:14px;font-weight:700;color:var(--primary-text-color)}
.tile .sub{max-width:100%;font-size:11.5px;line-height:1.2;color:var(--secondary-text-color);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tile.out .em{opacity:.42;filter:grayscale(.7)}
.tile.out .qty{color:var(--out);font-weight:500}
.tile .bang{position:absolute;top:-7px;right:-7px;z-index:1;display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--low);color:#1d1b16;font-size:15px;font-weight:800;line-height:1;box-shadow:0 0 0 2.5px var(--back),0 2px 6px rgba(0,0,0,.25)}
.side .tile .bang,.results .tile .bang{box-shadow:0 0 0 2.5px var(--primary-background-color,#fff),0 2px 6px rgba(0,0,0,.25)}
.tile.out .bang{background:var(--out);color:#fff}
.tile .incart{position:absolute;top:5px;left:5px;display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--surface);color:var(--primary-color,#03a9f4);box-shadow:0 1px 3px rgba(0,0,0,.15)}
.tile .badge{position:absolute;top:5px;right:5px;display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--c);color:var(--on-c)}
.tile.sugg{background:none;border:1.5px dashed var(--c3);border-radius:16px}
.tile.new{background:none;border:1.5px dashed var(--divider-color,rgba(0,0,0,.25));border-radius:16px}
.tile.tmp{opacity:.6;pointer-events:none}
.tile.entering{animation:pop .26s cubic-bezier(.2,.9,.3,1.3)}
.qty.bump b{display:inline-block;animation:bump .32s ease}
@keyframes pop{from{transform:scale(.6);opacity:0}}
@keyframes bump{40%{transform:scale(1.35)}}

/* columna lateral */
.side section+section{margin-top:28px}
.section-head{display:flex;align-items:center;gap:8px;margin:0 2px 10px}
.section-head h2{margin:0;font-size:15px;font-weight:500}
.section-head .n{font-size:13px;color:var(--secondary-text-color);font-variant-numeric:tabular-nums}
.section-head .grow{flex:1}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:8px}
.side .grid{padding:7px 7px 0 0}
.text-btn{display:inline-flex;align-items:center;gap:6px;border:0;background:none;color:var(--primary-color,#03a9f4);font-size:13.5px;font-weight:500;cursor:pointer;padding:6px 8px;border-radius:8px}
.text-btn:hover{background:rgba(127,127,127,.1)}
.more{display:block;margin:8px auto 0}
.muted{margin:0 2px;font-size:13.5px;line-height:1.45;color:var(--secondary-text-color)}
.moves{display:grid;gap:2px}
.move{display:flex;align-items:center;gap:12px;width:100%;min-height:52px;padding:6px 8px;border:0;border-radius:12px;background:none;text-align:left;cursor:pointer}
.move:hover{background:rgba(127,127,127,.08)}
.move .em{display:grid;place-items:center;flex:none;width:38px;height:38px;border-radius:11px;background:var(--c1);border:1px solid var(--c2);font-size:20px}
.move .txt{flex:1;min-width:0;display:flex;flex-direction:column;gap:1px}
.move .nm{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.move .sub{font-size:12.5px;color:var(--secondary-text-color);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.delta{flex:none;min-width:40px;text-align:right;font-size:15px;font-weight:600;font-variant-numeric:tabular-nums;color:var(--secondary-text-color)}
.delta.plus{color:var(--plus)}
.delta.zero{color:var(--out)}
.voice-tip{display:flex;gap:10px;align-items:flex-start;margin-top:24px;padding:12px 14px;border-radius:14px;background:var(--secondary-background-color,rgba(127,127,127,.08));font-size:13px;line-height:1.45;color:var(--secondary-text-color)}
.voice-tip svg{flex:none;color:var(--primary-color,#03a9f4);margin-top:1px}
.voice-tip q{color:var(--primary-text-color)}

/* vacío / error */
.empty{padding:28px 18px 34px;text-align:center;color:var(--secondary-text-color);font-size:14px;line-height:1.5}
.empty .big{font-size:44px;line-height:1}
.empty strong{display:block;margin:10px 0 4px;color:var(--primary-text-color);font-size:16px;font-weight:500}
.cupboard .empty+.plank{margin-top:6px}
.shelf.ghost{padding-top:56px}
.loading{padding:64px 16px;text-align:center;color:var(--secondary-text-color)}

/* aviso inferior */
.snackbar{position:absolute;left:50%;bottom:16px;z-index:6;display:flex;align-items:center;gap:8px;min-width:260px;max-width:calc(100% - 32px);padding:6px 6px 6px 16px;border-radius:12px;background:#2f3133;color:#f2f2f2;font-size:14px;box-shadow:0 6px 24px rgba(0,0,0,.28);transform:translate(-50%,24px);opacity:0;pointer-events:none;transition:transform .2s ease,opacity .2s ease}
.snackbar.show{transform:translate(-50%,0);opacity:1;pointer-events:auto}
.snackbar span{flex:1;padding:8px 0}
.snackbar button{border:0;background:none;color:#8fd0ff;font-weight:600;padding:8px 12px;border-radius:8px;cursor:pointer}
:host([mode=card]) .snackbar{position:sticky;transform:none;left:auto;margin:0 auto 12px;width:fit-content;display:none}
:host([mode=card]) .snackbar.show{display:flex}

/* hojas (diálogos) */
dialog{border:0;padding:0;width:min(520px,calc(100vw - 24px));max-height:min(90vh,820px);border-radius:22px;background:var(--surface);color:var(--primary-text-color,#1c1b1f);box-shadow:0 18px 50px rgba(0,0,0,.3);overflow:hidden}
dialog[open]{display:flex;flex-direction:column}
dialog::backdrop{background:rgba(0,0,0,.5)}
@media (max-width:600px){dialog{width:100vw;max-width:100vw;margin:auto 0 0;border-radius:22px 22px 0 0;max-height:94vh}}
.sheet-head{display:flex;align-items:center;gap:12px;padding:14px 10px 10px 16px}
.sheet-head h2{flex:1;margin:0;font-size:19px;font-weight:500;min-width:0}
.sheet-head .titles{flex:1;min-width:0}
.sheet-head .titles h2{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sheet-head .titles span{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--secondary-text-color);margin-top:2px}
.sheet-head .titles .dot{width:9px;height:9px;border-radius:50%;background:var(--c)}
.sheet-body{flex:1;overflow:auto;padding:4px 18px 10px}
.sheet-foot{display:flex;align-items:center;gap:8px;padding:12px 16px 16px;border-top:1px solid var(--divider-color,rgba(0,0,0,.1))}
.sheet-foot .grow{flex:1}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;height:40px;padding:0 20px;border-radius:20px;border:0;font-weight:500;cursor:pointer;background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff)}
.btn.quiet{background:none;color:var(--primary-color,#03a9f4)}
.btn.tonal{background:var(--secondary-background-color,rgba(127,127,127,.12));color:inherit}
.btn.danger{background:none;color:var(--error-color,#db4437);padding:0 12px}
.btn[disabled]{cursor:default}
.big-em{display:grid;place-items:center;width:56px;height:56px;border-radius:16px;border:1px solid var(--c2);background:var(--c1);font-size:32px;flex:none}
button.big-em{cursor:pointer}

.stock{display:flex;align-items:center;justify-content:center;gap:22px;margin:10px 0 2px}
.round{display:grid;place-items:center;width:56px;height:56px;border-radius:50%;border:1px solid var(--c2);background:var(--c1);color:var(--primary-text-color);cursor:pointer;flex:none;transition:transform .1s}
.round:active{transform:scale(.92)}
.round[disabled]{opacity:.35;cursor:default}
.count{min-width:96px;text-align:center}
.count .num{display:block;font-size:46px;font-weight:600;line-height:1.05;font-variant-numeric:tabular-nums}
.count .unit{display:block;font-size:13px;color:var(--secondary-text-color);min-height:16px}
.status{margin:8px 0 0;text-align:center;font-size:13.5px;color:var(--secondary-text-color)}
.status.warn,.status.out{display:flex;justify-content:center;align-items:center;gap:8px;color:var(--primary-text-color);font-weight:500}
.status .bang{display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--low);color:#1d1b16;font-size:13px;font-weight:800}
.status.out .bang{background:var(--out);color:#fff}
.quick{display:grid;grid-template-columns:1fr auto;gap:8px;margin:16px 0 4px}
.quick .btn{height:46px;border-radius:14px}
.quick .btn.done{background:var(--secondary-background-color,rgba(127,127,127,.12));color:var(--primary-text-color)}
.setting{display:flex;align-items:center;gap:12px;padding:14px 0;border-top:1px solid var(--divider-color,rgba(0,0,0,.08))}
.setting:first-of-type{margin-top:12px}
.setting .txt{flex:1;min-width:0}
.setting .t{display:block;font-size:14.5px}
.setting .s{display:block;font-size:12.5px;color:var(--secondary-text-color);margin-top:2px;line-height:1.35}
.mini{display:flex;align-items:center;gap:4px;flex:none}
.mini .icon-btn{width:34px;height:34px;border:1px solid var(--divider-color,rgba(0,0,0,.18))}
.mini .icon-btn[disabled]{opacity:.3;cursor:default}
.mini output{min-width:30px;text-align:center;font-size:17px;font-weight:600;font-variant-numeric:tabular-nums}
.mini output.off{font-size:13px;font-weight:400;color:var(--secondary-text-color);min-width:58px}
.input{width:100%;height:42px;padding:0 12px;border-radius:12px;border:1px solid var(--divider-color,rgba(0,0,0,.18));background:none;color:inherit;font:inherit;font-size:16px;outline:none}
.input:focus{border-color:var(--primary-color,#03a9f4)}
.setting .input{width:120px;flex:none}
.switch{position:relative;flex:none;width:44px;height:26px}
.switch input{position:absolute;inset:0;margin:0;opacity:0;cursor:pointer}
.switch span{position:absolute;inset:0;border-radius:13px;background:var(--divider-color,rgba(0,0,0,.25));transition:background .15s;pointer-events:none}
.switch span::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.3);transition:transform .15s}
.switch input:checked+span{background:var(--primary-color,#03a9f4)}
.switch input:checked+span::after{transform:translateX(18px)}
details{border-top:1px solid var(--divider-color,rgba(0,0,0,.08))}
summary{display:flex;align-items:center;gap:8px;padding:14px 0;cursor:pointer;list-style:none;font-size:14.5px}
summary::-webkit-details-marker{display:none}
summary svg{margin-left:auto;color:var(--secondary-text-color);transition:transform .15s}
details[open] summary svg{transform:rotate(180deg)}
.field{display:block;margin:0 0 16px}
.field>span{display:block;margin:0 0 8px;font-size:13px;color:var(--secondary-text-color)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.edit-head{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.emoji-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(42px,1fr));gap:2px;margin:-4px 0 16px;padding:8px;border-radius:14px;background:var(--secondary-background-color,rgba(127,127,127,.08));max-height:200px;overflow:auto}
.emoji-grid button{height:42px;border:0;background:none;border-radius:10px;font-size:24px;cursor:pointer}
.emoji-grid button:hover{background:rgba(127,127,127,.16)}
.emoji-grid .own{grid-column:1/-1;display:flex;gap:8px;align-items:center;margin-top:6px;font-size:13px;color:var(--secondary-text-color)}
.emoji-grid .own input{width:72px;text-align:center}
.history h3,.settings h3{margin:18px 0 6px;font-size:14.5px;font-weight:500}
.history .move{cursor:default;min-height:44px;padding:4px 0}
.history .move:hover{background:none}
.actions{display:grid;gap:8px;padding:4px 16px 20px}
.actions .btn{width:100%;height:48px;border-radius:14px;font-size:15px}
.actions .btn.tonal{font-weight:500}
.actions .btn.danger{background:color-mix(in srgb,var(--error-color,#db4437) 12%,transparent)}
.actions p{margin:0 4px 8px;font-size:13.5px;line-height:1.45;color:var(--secondary-text-color)}
.settings p{margin:0 0 10px;font-size:13px;line-height:1.45;color:var(--secondary-text-color)}
.settings .setting:first-of-type{margin-top:0}
.phrases{margin:6px 0 0;padding:0;list-style:none;display:grid;gap:6px}
.phrases li{font-size:13.5px}
.phrases q{color:var(--primary-text-color)}
q{quotes:"«" "»"}
.ignored{display:flex;flex-wrap:wrap;gap:8px}
@container (max-width:520px){
  .row,.grid{grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:6px}
  .tile{min-height:94px;padding:12px 3px 7px;gap:3px}
  .tile .em{font-size:28px}
  .tile .nm{font-size:12.5px}
  .cupboard{padding:4px 8px 8px;border-width:9px;border-top-width:12px}
  .plank{margin:0 -8px}
  .label{left:12px}
  .shelf+.shelf{margin-top:14px}
}
@media (prefers-reduced-motion:reduce){.tile,.snackbar,.round,.switch span,.switch span::after{transition:none}.tile.entering,.qty.bump b{animation:none}}
`;

/* ------------------------------------------------------- componente base */
class DespensaBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = null; // estado mostrado (con cambios optimistas)
    this._server = null; // último estado recibido del servidor
    this._catalog = [];
    this._catIndex = new Map();
    this._filter = null; // null | "low" | "cesta"
    this._query = "";
    this._seen = null;
    this._stocks = new Map();
    this._showAllMoves = false;
    this._narrow = false;
    this._config = {};
  }

  get mode() {
    return "panel";
  }

  /* ---- ciclo de vida */
  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._build();
    if (!this._unsub && !this._connecting && this.isConnected) this._connect();
    this._updateMenuButton();
  }
  get hass() {
    return this._hass;
  }
  set narrow(v) {
    this._narrow = v;
    this._updateMenuButton();
  }
  connectedCallback() {
    if (this._hass && !this._unsub && !this._connecting) this._connect();
  }
  disconnectedCallback() {
    if (this._unsub) {
      this._unsub();
      this._unsub = null;
    }
    clearTimeout(this._snackTimer);
  }

  async _connect() {
    this._connecting = true;
    try {
      if (!this._catalog.length) {
        const res = await this._hass.callWS({ type: "despensa/catalog" });
        this._catalog = res.catalog;
        this._catIndex = new Map(this._catalog.map((e) => [norm(e.name), e]));
        this._catStems = this._catalog.map((e) => [stems(e.name), e]);
        this._catStemIndex = new Map(this._catStems.map(([w, e]) => [w.join(" "), e]));
      }
      const unsub = await this._hass.connection.subscribeMessage(
        (state) => {
          this._server = state;
          this._state = state;
          this._error = null;
          this._render();
        },
        { type: "despensa/subscribe" }
      );
      if (!this.isConnected) unsub();
      else this._unsub = unsub;
    } catch (err) {
      this._error = err && err.code === "not_loaded" ? "not_loaded" : (err && err.message) || String(err);
      this._render();
    } finally {
      this._connecting = false;
    }
  }

  /* ---- esqueleto */
  _build() {
    const card = this.mode === "card";
    this.setAttribute("mode", this.mode);
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      ${card ? "<ha-card>" : ""}
      <div class="app" lang="es">
        <header class="toolbar">
          ${card ? "" : `<button class="icon-btn menu" data-action="menu" aria-label="Menú" hidden>${svg(P.menu)}</button>`}
          <h1><span class="title">${esc(this._config.title || "Despensa")}</span><small class="count"></small></h1>
          <button class="icon-btn" data-action="settings" aria-label="Ajustes de Despensa" title="Ajustes">${svg(P.cog)}</button>
        </header>
        <div class="scroller">
          <div class="layout">
            <div class="main">
              <div class="addwrap">
                <label class="addbar">
                  ${svg(P.search, 22)}
                  <input type="text" enterkeyhint="done" autocomplete="off" autocapitalize="sentences" spellcheck="false"
                    placeholder="Añadir a la despensa…" aria-label="Añadir a la despensa">
                  <button class="icon-btn clear" data-action="clear" aria-label="Borrar texto" hidden>${svg(P.close, 20)}</button>
                </label>
              </div>
              <div class="results" hidden></div>
              <div class="filters" role="toolbar" aria-label="Filtrar"></div>
              <div class="list"><div class="loading">Abriendo la despensa…</div></div>
            </div>
            <div class="side"></div>
          </div>
        </div>
        <div class="snackbar" role="status" aria-live="polite"><span></span><button type="button" data-action="snack" hidden></button></div>
        <dialog></dialog>
      </div>
      ${card ? "</ha-card>" : ""}`;
    const $ = (s) => this.shadowRoot.querySelector(s);
    this.$ = {
      input: $(".addbar input"), clear: $(".clear"), results: $(".results"), filters: $(".filters"),
      list: $(".list"), side: $(".side"), count: $(".count"), menu: $(".menu"), snack: $(".snackbar"),
      dialog: $("dialog"),
    };
    const root = this.shadowRoot;
    root.addEventListener("click", (e) => this._onClick(e));
    root.addEventListener("keydown", (e) => this._onKey(e));
    root.addEventListener("input", (e) => this._onInput(e));
    root.addEventListener("change", (e) => this._onInput(e));
    this.$.dialog.addEventListener("close", () => {
      if (this._sheet === "item") this._commitEdit();
      this._sheet = null;
    });
    this.$.dialog.addEventListener("click", (e) => {
      if (e.target === this.$.dialog) this.$.dialog.close(); // clic en el fondo
    });
    this._updateMenuButton();
  }

  _updateMenuButton() {
    if (!this.$ || !this.$.menu) return;
    const hidden = this._hass && this._hass.dockedSidebar === "always_hidden";
    this.$.menu.hidden = !(this._narrow || hidden);
  }

  /* ---- datos auxiliares */
  get _depts() {
    return this._state ? this._state.departments : [];
  }
  _dept(id) {
    const d = this._depts;
    return d.find((x) => x.id === id) || d.find((x) => x.id === "otros") || d[d.length - 1] || { id: "otros", name: "Otros", color: "#78909C", icon: "🛒" };
  }
  get _cestaOn() {
    return !!(this._state && this._state.cesta && this._state.cesta.available);
  }
  _inCesta(it) {
    return this._cestaOn && this._state.cesta.in_list.includes(norm(it.name));
  }
  _item(id) {
    return this._state && this._state.items.find((i) => i.id === id);
  }
  _findItem(name) {
    const key = norm(name);
    const items = this._state.items;
    const s = stems(name).join(" ");
    return items.find((i) => norm(i.name) === key) || items.find((i) => stems(i.name).join(" ") === s);
  }
  /* Baldas de la tarjeta (opción departments: ids o nombres) */
  get _cardDepts() {
    const want = this._config.departments;
    if (!Array.isArray(want) || !want.length) return null;
    const keys = new Set(want.map(norm));
    return new Set(this._depts.filter((d) => keys.has(norm(d.id)) || keys.has(norm(d.name))).map((d) => d.id));
  }
  _deptOf(it) {
    return this._dept(it.department).id;
  }
  _scoped() {
    const only = this._cardDepts;
    return only ? this._state.items.filter((i) => only.has(this._deptOf(i))) : this._state.items;
  }
  _visible() {
    const items = this._scoped();
    if (this._filter === "low") return items.filter(isLow);
    if (this._filter === "cesta") return items.filter((i) => this._inCesta(i));
    return items;
  }
  /* Producto del catálogo para un nombre libre */
  _lookup(name) {
    let key = norm(name);
    if (!this._catIndex.has(key)) {
      const same = this._catStemIndex && this._catStemIndex.get(stems(name).join(" "));
      if (same) key = norm((name = same.name));
    }
    const cat = this._catIndex.get(key) || this._guess(name);
    return {
      key,
      name: (this._catIndex.get(key) || {}).name || cap(name),
      icon: (cat && cat.icon) || "🛒",
      department: (cat && cat.department) || "otros",
      known: this._catIndex.has(key),
    };
  }
  _guess(name) {
    const words = stems(name);
    if (!words.length || !this._catStems) return null;
    let best = null;
    let bestScore = 0;
    for (const [cw, entry] of this._catStems) {
      if (!cw.length || cw.length > words.length) continue;
      for (let s = 0; s + cw.length <= words.length; s++) {
        if (cw.every((w, i) => words[s + i] === w)) {
          let score = cw.reduce((n, w) => n + w.length, 0) * 10 + (s === 0 ? 5 : 0);
          if (cw.length === words.length) score += 1000;
          if (score > bestScore) [best, bestScore] = [entry, score];
          break;
        }
      }
    }
    return best;
  }

  _search(q) {
    const parts = q.split(",").map((s) => s.trim()).filter(Boolean);
    const view = (name) => {
      const it = this._findItem(name);
      if (it) return { ...it, exists: true, key: norm(it.name) };
      return { ...this._lookup(name), exists: false, isNew: true };
    };
    if (parts.length > 1) return parts.map(view);
    const nq = norm(q);
    if (!nq) return [];
    const pool = new Map();
    for (const e of this._catalog) pool.set(norm(e.name), { ...e, exists: false });
    for (const it of this._state.items) pool.set(norm(it.name), { ...it, exists: true });
    const found = [];
    for (const [k, e] of pool) {
      let s = 0;
      if (k === nq) s = 100;
      else if (k.startsWith(nq)) s = 80;
      else if (k.split(" ").some((w) => w.startsWith(nq))) s = 60;
      else if (nq.length > 2 && k.includes(nq)) s = 40;
      if (s) found.push({ ...e, key: k, score: s + (e.exists ? 15 : 0) });
    }
    found.sort((a, b) => b.score - a.score || byName(a, b));
    const top = found.slice(0, 11);
    const typed = view(q);
    if (!top.some((r) => r.key === typed.key)) {
      if (top.length) top.push(typed);
      else top.unshift(typed);
    }
    return top;
  }

  /* ------------------------------------------------------------ pintado */
  _tile(it, o = {}) {
    const d = this._dept(it.department);
    const low = isLow(it);
    const out = it.stock <= 0;
    const cls = ["tile", out ? "out" : "", it.id && it.id.startsWith("tmp-") ? "tmp" : "", o.enter ? "entering" : "", o.cls || ""].join(" ").trim();
    const unit = unitFor(it.unit, it.stock);
    const inCesta = this._inCesta(it);
    const label = `${it.name}: ${out ? "agotado" : qty(it.stock, it.unit)}${low ? ", por reponer" : ""}${inCesta ? ", en la Cesta" : ""}.`;
    const bump = o.bump ? " bump" : "";
    return `<button type="button" class="${cls}" style="${tone(d.color)}" data-action="${o.action || "open"}" data-id="${esc(it.id)}" aria-label="${esc(label)}">
      ${inCesta ? `<span class="incart" title="En la Cesta">${svg(P.cartCheck, 14)}</span>` : ""}
      ${low ? `<span class="bang" title="${out ? "Agotado" : "Por reponer"}">!</span>` : ""}
      <span class="em">${esc(it.icon)}</span>
      <span class="nm">${soft(it.name)}</span>
      <span class="qty${bump}">${out ? "Agotado" : `<b>${it.stock}</b>${unit ? ` ${esc(unit)}` : ""}`}</span>
    </button>`;
  }

  _render() {
    if (!this.$) return;
    if (this._error) {
      const msg =
        this._error === "not_loaded"
          ? "Despensa no está configurada. Añádela en Ajustes → Dispositivos y servicios → Añadir integración."
          : `No se pudo cargar: ${this._error}`;
      this.$.list.innerHTML = `<div class="empty"><div class="big emoji">🗄️</div><strong>Sin conexión con la despensa</strong>${esc(msg)}</div>`;
      return;
    }
    if (!this._state) return;
    const n = this._scoped().length;
    this.$.count.textContent = n ? `${n} ${n === 1 ? "producto" : "productos"}` : "";
    this._renderFilters();
    this._renderCupboard();
    this._renderResults();
    this._renderSide();
    if (this._sheet === "item") this._renderItemLive();
    if (this._sheet === "settings") this._renderSettings();
    this._seen = new Set(this._state.items.map((i) => i.id));
    this._stocks = new Map(this._state.items.map((i) => [i.id, i.stock]));
  }

  _renderFilters() {
    const items = this._scoped();
    const low = items.filter(isLow).length;
    const inCesta = items.filter((i) => this._inCesta(i)).length;
    if (this._filter === "cesta" && !this._cestaOn) this._filter = null;
    const chip = (id, content, n) =>
      `<button type="button" class="chip" data-action="filter" data-id="${id}" aria-pressed="${(this._filter || "") === id}">${content} <span class="n">${n}</span></button>`;
    this.$.filters.innerHTML = items.length
      ? chip("", "Todo", items.length) +
        chip("low", `<span class="bang" aria-hidden="true">!</span>Por reponer`, low) +
        (this._cestaOn ? chip("cesta", `${svg(P.cartCheck, 18)}En la Cesta`, inCesta) : "")
      : "";
  }

  _renderCupboard() {
    const items = this._visible();
    const plank = `<div class="plank"></div>`;
    if (!items.length) {
      const empty = !this._scoped().length;
      const msg = empty
        ? `<div class="big emoji">🫙</div><strong>La despensa está vacía</strong>Busca arriba lo que tienes en casa${this._cestaOn ? " o marca algo como comprado en la Cesta: aparecerá aquí, en su balda" : ""}.`
        : this._filter === "low"
          ? `<div class="big emoji">👌</div><strong>Nada por reponer</strong>Ningún producto ha llegado a su stock mínimo.`
          : `<div class="big emoji">🛒</div><strong>Nada de la despensa en la Cesta</strong>Abre un producto y toca «Añadir a la Cesta».`;
      this.$.list.innerHTML = `<div class="cupboard"><div class="empty">${msg}</div>${plank}<div class="shelf ghost" aria-hidden="true">${plank}</div></div>`;
      return;
    }
    const depts = this._depts;
    const groups = depts
      .map((d) => ({ d, items: items.filter((it) => this._deptOf(it) === d.id).sort(byName) }))
      .filter((g) => g.items.length);
    const fresh = (id) => this._seen && !this._seen.has(id);
    const bumped = (it) => this._stocks.has(it.id) && this._stocks.get(it.id) !== it.stock;
    this.$.list.innerHTML = `<div class="cupboard">${groups
      .map(
        (g) => `<section class="shelf" style="${tone(g.d.color)}" aria-label="Balda ${esc(g.d.name)}">
          <div class="row">${g.items.map((it) => this._tile(it, { enter: fresh(it.id), bump: bumped(it) })).join("")}</div>
          <div class="plank"><span class="label"><span class="ico emoji" aria-hidden="true">${esc(g.d.icon)}</span><span class="txt">${esc(g.d.name)}</span><span class="n">${g.items.length}</span></span></div>
        </section>`
      )
      .join("")}</div>`;
  }

  _renderResults() {
    const q = this._query;
    this.$.clear.hidden = !q;
    if (!q.trim()) {
      this.$.results.hidden = true;
      this.$.results.innerHTML = "";
      return;
    }
    const tiles = this._search(q)
      .map((r) => {
        const d = this._dept(r.department);
        const sub = r.exists ? (r.stock > 0 ? `Tienes ${qty(r.stock, r.unit)}` : "Agotado") : r.isNew && !r.known ? "Nuevo" : "";
        return `<button type="button" class="tile ${r.exists || r.known || !r.isNew ? "sugg" : "new"}" style="${tone(d.color)}" data-action="add-name" data-name="${esc(r.name)}"
            aria-label="${esc(r.exists ? `Sumar uno a ${r.name}` : `Añadir ${r.name} a la despensa`)}">
          <span class="badge">${svg(P.plus, 14)}</span>
          <span class="em">${esc(r.icon)}</span><span class="nm">${soft(r.name)}</span>
          ${sub ? `<span class="sub">${esc(sub)}</span>` : ""}</button>`;
      })
      .join("");
    this.$.results.hidden = false;
    this.$.results.innerHTML = `<div class="grid">${tiles}</div>
      <p class="hint">${q.includes(",") ? "Pulsa Intro para añadirlos todos." : "Si ya lo tienes, suma uno. Separa con comas para añadir varios."}</p>`;
  }

  _moveRow(e, inSheet = false) {
    const d = this._dept(e.department);
    const sign = e.delta > 0 ? "+" : e.delta < 0 ? MINUS : "";
    const cls = e.kind === "empty" ? "zero" : e.delta > 0 ? "plus" : "";
    const what = (e.kind === "set" ? `Corregido a ${e.stock}` : KIND[e.kind] || "Cambio") + (SOURCE[e.source] || "");
    const delta = e.kind === "empty" ? "0" : `${sign}${Math.abs(e.delta)}`;
    if (inSheet)
      return `<div class="move"><span class="txt"><span class="nm">${esc(what)}</span><span class="sub">${esc(cap(ago(e.ts)))}</span></span><span class="delta ${cls}">${delta}</span></div>`;
    const sub = `${what}, ${ago(e.ts)}`;
    return `<button type="button" class="move" style="${tone(d.color)}" data-action="open" data-id="${esc(e.item_id)}" aria-label="${esc(`${e.name}: ${sub}`)}">
      <span class="em emoji" aria-hidden="true">${esc(e.icon)}</span>
      <span class="txt"><span class="nm">${esc(e.name)}</span><span class="sub">${esc(sub)}</span></span>
      <span class="delta ${cls}">${delta}</span></button>`;
  }

  _renderSide() {
    const cfg = this._config;
    let html = "";
    if (cfg.show_low !== false) {
      const low = this._scoped().filter(isLow).sort(byName);
      const missing = low.filter((i) => !this._inCesta(i)).length;
      html += `<section><div class="section-head"><h2>Por reponer</h2>${low.length ? `<span class="n">${low.length}</span>` : ""}<span class="grow"></span>
          ${this._cestaOn && missing ? `<button type="button" class="text-btn" data-action="cesta-low">${svg(P.cartPlus, 18)}Añadir ${missing === 1 ? "a la Cesta" : `los ${missing} a la Cesta`}</button>` : ""}</div>
        ${low.length ? `<div class="grid">${low.map((it) => this._tile(it)).join("")}</div>` : `<p class="muted">Nada ha llegado a su mínimo. Cuando algo llegue, aparecerá aquí con una <strong>!</strong>.</p>`}
      </section>`;
    }
    if (cfg.show_log !== false) {
      const only = this._cardDepts;
      const log = this._state.log.filter((e) => !only || only.has(this._dept(e.department).id));
      const limit = this._showAllMoves ? log.length : 8;
      html += `<section><div class="section-head"><h2>Movimientos</h2><span class="grow"></span>
          ${log.length ? `<button type="button" class="text-btn" data-action="clear-log">Vaciar</button>` : ""}</div>
        ${log.length ? `<div class="moves">${log.slice(0, limit).map((e) => this._moveRow(e)).join("")}</div>
          ${log.length > limit ? `<button type="button" class="text-btn more" data-action="more-moves">Ver los ${log.length}</button>` : ""}`
        : `<p class="muted">Aquí verás lo que se usa en casa y lo que llega de la Cesta.</p>`}
      </section>`;
      if (this._state.voice_active && this.mode === "panel")
        html += `<div class="voice-tip">${svg(P.mic, 20)}<span>Con Assist puedes decir <q>He usado dos latas de atún</q>, <q>Se ha acabado la leche</q> o <q>¿Qué falta?</q></span></div>`;
    }
    this.$.side.innerHTML = html;
    this.$.side.hidden = !html;
  }

  /* ------------------------------------------------------------ eventos */
  _onInput(e) {
    const t = e.composedPath()[0];
    if (t === this.$.input) {
      if (e.type !== "input" || t.value === this._query) return;
      this._query = t.value;
      if (this._state) this._renderResults();
      return;
    }
    if (this._sheet && t.dataset) this._sheetInput(t, e.type);
  }

  _onKey(e) {
    const t = e.composedPath()[0];
    if (t === this.$.input) {
      if (e.key === "Enter" && !e.isComposing) {
        e.preventDefault();
        this._submitQuery();
      } else if (e.key === "Escape") {
        this._setQuery("");
      }
    }
  }

  _onClick(e) {
    const el = e.target.closest("[data-action]");
    if (!el || el.disabled) return;
    const { action, id, name } = el.dataset;
    switch (action) {
      case "menu":
        this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
        break;
      case "settings":
        this._openSettings();
        break;
      case "clear":
        this._setQuery("");
        this.$.input.focus();
        break;
      case "filter":
        this._filter = id || null;
        this._render();
        break;
      case "open":
        this._openItem(id);
        break;
      case "add-name":
        this._addName(name);
        this._setQuery("");
        if (matchMedia("(hover:hover)").matches) this.$.input.focus();
        break;
      case "cesta-low":
        this._toCestaLow();
        break;
      case "clear-log":
        this._optimistic((st) => (st.log = []));
        this._ws({ type: "despensa/log/clear" });
        break;
      case "more-moves":
        this._showAllMoves = true;
        this._renderSide();
        break;
      case "snack":
        clearTimeout(this._snackTimer);
        this.$.snack.classList.remove("show");
        if (this._snackFn) this._snackFn();
        this._snackFn = null;
        break;
      default:
        if (this._sheet) this._sheetAction(action, el);
    }
  }

  _setQuery(q) {
    this._query = q;
    this.$.input.value = q;
    this._renderResults();
  }
  _submitQuery() {
    const q = this._query.trim();
    if (!q || !this._state) return;
    for (const part of q.split(",").map((s) => s.trim()).filter(Boolean)) this._addName(part);
    this._setQuery("");
  }

  /* ------------------------------------------------------- operaciones */
  async _ws(msg) {
    try {
      return await this._hass.callWS(msg);
    } catch (err) {
      this._state = this._server;
      this._render();
      this._toast(`No se pudo guardar: ${(err && err.message) || err}`);
      return null;
    }
  }
  _optimistic(fn) {
    const st = structuredClone(this._state);
    fn(st);
    this._state = st;
    this._render();
  }
  _setStock(st, id, stock) {
    const it = st.items.find((i) => i.id === id);
    if (it) it.stock = Math.max(0, stock);
    return it;
  }

  _addName(name) {
    if (!name || !this._state) return;
    const it = this._findItem(name);
    if (it) {
      if (it.id.startsWith("tmp-")) return;
      const before = it.stock;
      this._optimistic((st) => this._setStock(st, it.id, before + 1));
      const p = this._ws({ type: "despensa/item/adjust", item_id: it.id, delta: 1 });
      this._toast(`${it.name}: ahora ${qty(before + 1, it.unit)}`, "Deshacer", () => this._undoFrom(p));
      return;
    }
    const l = this._lookup(name);
    if (this._findItem(l.name)) return this._addName(l.name);
    this._optimistic((st) =>
      st.items.push({
        id: `tmp-${Math.random().toString(36).slice(2)}`, name: l.name, icon: l.icon, department: l.department,
        stock: 1, min_stock: st.settings.default_min, unit: "", pack: 1,
      })
    );
    const p = this._ws({ type: "despensa/item/create", name: l.name, stock: 1 });
    this._toast(`Añadido a la despensa: ${l.name}`, "Deshacer", () => this._undoFrom(p));
  }

  async _undoFrom(promise) {
    const res = await promise;
    if (res && res.log && res.log.id) this._ws({ type: "despensa/log/undo", log_id: res.log.id });
  }

  _adjust(id, delta) {
    const it = this._item(id);
    if (!it || id.startsWith("tmp-")) return;
    const target = Math.max(0, it.stock + delta);
    if (target === it.stock) return;
    this._optimistic((st) => this._setStock(st, id, target));
    this._ws({ type: "despensa/item/adjust", item_id: id, delta });
  }

  _empty(id) {
    const it = this._item(id);
    if (!it) return;
    this._optimistic((st) => this._setStock(st, id, 0));
    const p = this._ws({ type: "despensa/item/empty", item_id: id });
    this._toast(`Se acabó: ${it.name}`, "Deshacer", () => this._undoFrom(p));
  }

  _delete(id, ignore) {
    const it = this._item(id);
    if (!it) return;
    this._optimistic((st) => (st.items = st.items.filter((i) => i.id !== id)));
    this._ws({ type: "despensa/item/delete", item_id: id, ignore });
    this._toast(`Quitado de la despensa: ${it.name}`, "Deshacer", () => this._ws({ type: "despensa/item/restore", item_id: id }));
  }

  async _toCesta(id) {
    const it = this._item(id);
    if (!it || !this._cestaOn) return;
    this._optimistic((st) => st.cesta.in_list.push(norm(it.name)));
    const res = await this._ws({ type: "despensa/cesta/add", item_id: id });
    if (res && !this._sheet) this._toast(`Añadido a la Cesta: ${it.name}`);
  }

  async _toCestaLow() {
    const res = await this._ws({ type: "despensa/cesta/add_low" });
    if (!res) return;
    const n = res.added.length;
    this._toast(n ? `Añadido${n === 1 ? "" : "s"} a la Cesta: ${res.added.join(", ")}` : "Ya estaba todo en la Cesta");
  }

  _toast(text, label, fn) {
    const s = this.$.snack;
    s.querySelector("span").textContent = text;
    const b = s.querySelector("button");
    b.hidden = !label;
    b.textContent = label || "";
    this._snackFn = fn || null;
    s.classList.add("show");
    clearTimeout(this._snackTimer);
    this._snackTimer = setTimeout(() => {
      s.classList.remove("show");
      this._snackFn = null;
    }, 5000);
  }

  /* -------------------------------------------------------------- hojas */
  _openSheet(kind, html) {
    const d = this.$.dialog;
    this._sheet = kind;
    d.innerHTML = html;
    if (!d.open) d.showModal();
  }

  _openItem(id) {
    const it = this._item(id);
    if (!it || id.startsWith("tmp-")) return;
    this._edit = { id, name: it.name, icon: it.icon, department: it.department, min_stock: it.min_stock ?? null, unit: it.unit || "", pack: it.pack || 1, dirty: false, lastMin: it.min_stock ?? 1 };
    const emojis = [...new Set([...this._catalog.map((e) => e.icon), ...this._depts.map((d) => d.icon), ...EXTRA_EMOJI.match(/\p{Extended_Pictographic}️?/gu)])];
    this._openSheet(
      "item",
      `<div class="sheet-head">
        <span class="big-em emoji" aria-hidden="true"></span>
        <div class="titles"><h2></h2><span><span class="dot"></span><span class="dname"></span></span></div>
        <button type="button" class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button>
      </div>
      <div class="sheet-body">
        <div class="stock">
          <button type="button" class="round" data-action="dec" aria-label="Usar uno">${svg(P.minus, 28)}</button>
          <div class="count" aria-live="polite"><span class="num"></span><span class="unit"></span></div>
          <button type="button" class="round" data-action="inc" aria-label="Añadir uno">${svg(P.plus, 28)}</button>
        </div>
        <p class="status"></p>
        <div class="quick"></div>
        <div class="setting">
          <span class="txt"><span class="t">Avisar cuando queden</span><span class="s">Al llegar a este número sale la <strong>!</strong> y pasa a «Por reponer»</span></span>
          <span class="mini"><button type="button" class="icon-btn" data-action="min-dec" aria-label="Bajar el mínimo">${svg(P.minus, 18)}</button><output class="min-out"></output><button type="button" class="icon-btn" data-action="min-inc" aria-label="Subir el mínimo">${svg(P.plus, 18)}</button></span>
        </div>
        <div class="setting">
          <span class="txt"><span class="t">Sin aviso</span><span class="s">No avisar aunque se acabe</span></span>
          <label class="switch"><input type="checkbox" role="switch" data-field="nomin" aria-label="Sin aviso de stock mínimo"><span></span></label>
        </div>
        ${this._cestaOn ? `<div class="setting">
          <span class="txt"><span class="t">Cada compra en la Cesta suma</span><span class="s">Por ejemplo, 6 si siempre compras el pack de 6</span></span>
          <span class="mini"><button type="button" class="icon-btn" data-action="pack-dec" aria-label="Menos">${svg(P.minus, 18)}</button><output class="pack-out"></output><button type="button" class="icon-btn" data-action="pack-inc" aria-label="Más">${svg(P.plus, 18)}</button></span>
        </div>` : ""}
        <div class="setting">
          <span class="txt"><span class="t">Se cuenta en</span><span class="s">Bricks, latas, paquetes… o vacío para unidades</span></span>
          <input class="input" data-field="unit" list="despensa-units" maxlength="20" placeholder="uds" aria-label="Unidad">
          <datalist id="despensa-units">${UNITS.map((u) => `<option value="${u}">`).join("")}</datalist>
        </div>
        <details>
          <summary>Nombre, icono y balda ${svg(P.chevron, 20)}</summary>
          <div class="edit-head">
            <button type="button" class="big-em emoji pick-em" data-action="emojis" aria-label="Cambiar icono" title="Cambiar icono"></button>
            <input class="input" data-field="name" maxlength="120" aria-label="Nombre">
          </div>
          <div class="emoji-grid" hidden>${emojis.map((x) => `<button type="button" class="emoji" data-action="pick" data-emoji="${esc(x)}">${x}</button>`).join("")}
            <label class="own">Otro: <input class="input emoji" data-field="icon" maxlength="16" placeholder="😀"></label></div>
          <div class="field"><span>Balda</span><div class="chips dept-chips"></div></div>
        </details>
        <div class="history"></div>
      </div>
      <div class="sheet-foot"><button type="button" class="btn danger" data-action="ask-delete">Quitar de la despensa</button><span class="grow"></span>
        <button type="button" class="btn" data-action="close">Hecho</button></div>`
    );
    const d = this.$.dialog;
    d.querySelector('[data-field="name"]').value = it.name;
    d.querySelector('[data-field="unit"]').value = it.unit || "";
    this._renderEditFields();
    this._renderItemLive();
  }

  /* Partes de la ficha que cambian con el servidor (stock, Cesta, historial) */
  _renderItemLive() {
    const d = this.$.dialog;
    const e = this._edit;
    const real = this._item(e.id);
    if (!real) {
      this._sheet = null;
      d.close();
      return;
    }
    const it = { ...real, min_stock: e.min_stock }; // el mínimo que se está editando
    const low = isLow(it);
    const out = it.stock <= 0;
    const unit = e.unit.trim();
    d.querySelector(".num").textContent = it.stock;
    d.querySelector(".count .unit").textContent = unitFor(unit, it.stock) || (it.stock === 1 ? "unidad" : "unidades");
    d.querySelector('[data-action="dec"]').disabled = out;
    const status = d.querySelector(".status");
    const min = e.min_stock;
    status.className = `status ${out && low ? "out" : low ? "warn" : ""}`;
    status.innerHTML = low
      ? `<span class="bang" aria-hidden="true">!</span>${out ? "Se ha acabado" : `Por reponer: el mínimo es ${min}`}`
      : out
        ? "Se ha acabado"
        : min === null
          ? "Sin aviso de stock mínimo"
          : min === 0
            ? "Te avisará cuando se acabe"
            : `Te avisará cuando queden ${min}`;
    const quick = d.querySelector(".quick");
    let cestaBtn = "";
    if (this._cestaOn)
      cestaBtn = this._inCesta(it)
        ? `<button type="button" class="btn done" disabled>${svg(P.cartCheck, 20)}Ya está en la Cesta</button>`
        : `<button type="button" class="btn" data-action="to-cesta">${svg(P.cartPlus, 20)}Añadir a la Cesta</button>`;
    quick.style.gridTemplateColumns = cestaBtn ? "1fr auto" : "1fr";
    quick.innerHTML = cestaBtn + `<button type="button" class="btn tonal" data-action="empty" ${out ? "disabled" : ""}>Se ha acabado</button>`;
    const moves = this._state.log.filter((x) => x.item_id === it.id).slice(0, 5);
    d.querySelector(".history").innerHTML = moves.length
      ? `<h3>Últimos movimientos</h3><div class="moves">${moves.map((m) => this._moveRow(m, true)).join("")}</div>`
      : "";
  }

  /* Campos que edita la persona (no se pisan con lo que llega del servidor) */
  _renderEditFields() {
    const d = this.$.dialog;
    const e = this._edit;
    const dept = this._dept(e.department);
    const head = d.querySelector(".sheet-head");
    head.setAttribute("style", tone(dept.color));
    head.querySelector(".big-em").textContent = e.icon;
    head.querySelector("h2").textContent = e.name;
    head.querySelector(".dname").textContent = dept.name;
    d.querySelector(".sheet-body").setAttribute("style", tone(dept.color));
    d.querySelector(".pick-em").textContent = e.icon;
    const minOut = d.querySelector(".min-out");
    minOut.textContent = e.min_stock === null ? "—" : e.min_stock;
    d.querySelector('[data-action="min-dec"]').disabled = e.min_stock === null || e.min_stock <= 0;
    d.querySelector('[data-action="min-inc"]').disabled = e.min_stock === null;
    d.querySelector('[data-field="nomin"]').checked = e.min_stock === null;
    const pack = d.querySelector(".pack-out");
    if (pack) {
      pack.textContent = e.pack;
      d.querySelector('[data-action="pack-dec"]').disabled = e.pack <= 1;
    }
    d.querySelector(".dept-chips").innerHTML = this._depts
      .map(
        (x) => `<button type="button" class="chip dept" style="${tone(x.color)}" data-action="pick-dept" data-id="${esc(x.id)}" aria-pressed="${e.department === x.id}">
          <span class="dot"></span>${esc(x.name)}</button>`
      )
      .join("");
  }

  _commitEdit() {
    const e = this._edit;
    if (!e || !e.dirty) return;
    const it = this._item(e.id);
    if (!it) return;
    const name = cap(e.name) || it.name;
    const icon = (e.icon || "").trim() || it.icon;
    const changes = { name, icon, department: e.department, min_stock: e.min_stock, unit: e.unit.trim(), pack: e.pack };
    e.dirty = false;
    this._optimistic((st) => {
      const x = st.items.find((y) => y.id === e.id);
      if (x) Object.assign(x, changes);
    });
    this._ws({ type: "despensa/item/update", item_id: e.id, ...changes });
  }

  _openDelete() {
    const e = this._edit;
    const it = this._item(e.id);
    if (!it) return;
    this._commitEdit();
    this._sheet = "confirm";
    this.$.dialog.innerHTML = `<div class="sheet-head" style="${tone(this._dept(it.department).color)}"><span class="big-em emoji" aria-hidden="true">${esc(it.icon)}</span>
        <h2>¿Quitar ${esc(it.name)}?</h2><button type="button" class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button></div>
      <div class="actions">
        <p>Desaparece del armario y de «Por reponer». Su historial de movimientos se conserva.</p>
        <button type="button" class="btn danger" data-action="delete">Quitar de la despensa</button>
        ${this._cestaOn ? `<button type="button" class="btn tonal" data-action="delete-ignore">Quitar y no añadirlo al comprarlo en la Cesta</button>` : ""}
        <button type="button" class="btn quiet" data-action="back">Cancelar</button>
      </div>`;
  }

  _openSettings() {
    if (!this._state) return;
    this._openSheet(
      "settings",
      `<div class="sheet-head"><h2>Ajustes de la despensa</h2><button type="button" class="icon-btn" data-action="close" aria-label="Cerrar">${svg(P.close)}</button></div>
       <div class="sheet-body settings"></div>
       <div class="sheet-foot"><span class="grow"></span><button type="button" class="btn" data-action="close">Hecho</button></div>`
    );
    this._renderSettings();
  }

  _renderSettings() {
    const st = this._state;
    const s = st.settings;
    const body = this.$.dialog.querySelector(".settings");
    if (!body) return;
    const sw = (key, title, sub, disabled = false) => `<div class="setting">
        <span class="txt"><span class="t">${title}</span><span class="s">${sub}</span></span>
        <label class="switch"><input type="checkbox" role="switch" data-setting="${key}" ${s[key] ? "checked" : ""} ${disabled ? "disabled" : ""} aria-label="${esc(title)}"><span></span></label>
      </div>`;
    const min = s.default_min;
    body.innerHTML = `
      <h3>Productos nuevos</h3>
      <div class="setting">
        <span class="txt"><span class="t">Avisar cuando queden</span><span class="s">Mínimo con el que empieza cada producto nuevo; luego lo cambias en cada uno</span></span>
        <span class="mini"><button type="button" class="icon-btn" data-action="dmin-dec" aria-label="Bajar" ${min === null || min <= 0 ? "disabled" : ""}>${svg(P.minus, 18)}</button><output class="${min === null ? "off" : ""}">${min === null ? "Sin aviso" : min}</output><button type="button" class="icon-btn" data-action="dmin-inc" aria-label="Subir">${svg(P.plus, 18)}</button></span>
      </div>
      <h3>Cesta</h3>
      ${st.cesta.available
        ? `<p>Lo que marcas como comprado en la Cesta se suma aquí, y si lo deshaces allí, se resta. Las baldas y sus colores son los departamentos de Cesta: cámbialos en sus ajustes.</p>
           ${sw("add_from_cesta", "Añadir lo que no está en la despensa", "Si compras algo nuevo, se crea en su balda")}
           ${sw("auto_cesta", "Añadir a la Cesta al llegar al mínimo", "Sin tener que pulsar nada")}
           ${st.ignored.length ? `<h3>No se añaden al comprarlos</h3><div class="ignored">${st.ignored.map((n) => `<button type="button" class="chip" data-action="unignore" data-name="${esc(n)}">${esc(n)} ${svg(P.close, 16)}</button>`).join("")}</div>` : ""}`
        : `<p>Instala Cesta (la lista de la compra) para que lo que compras se sume solo y para poder añadir a la lista lo que falta.</p>`}
      <h3>Voz</h3>
      ${sw("voice", "Frases para Assist", st.voice_active ? "Activas" : s.voice ? "Se activarán cuando Assist esté disponible" : "Desactivadas")}
      <ul class="phrases">
        <li><q>He usado dos latas de atún</q></li>
        <li><q>Se ha acabado la leche</q></li>
        <li><q>He comprado tres paquetes de arroz</q></li>
        <li><q>¿Cuánto aceite queda?</q></li>
        <li><q>¿Qué falta en la despensa?</q></li>
        ${st.cesta.available ? "<li><q>Añade lo que falta a la cesta</q></li>" : ""}
      </ul>`;
  }

  _setting(key, value) {
    this._optimistic((st) => (st.settings[key] = value));
    this._ws({ type: "despensa/settings/set", [key]: value });
    if (this._sheet === "settings") this._renderSettings();
  }

  _sheetInput(t, type) {
    if (this._sheet === "item" && t.dataset.field) {
      const e = this._edit;
      const f = t.dataset.field;
      if (f === "nomin") {
        if (t.checked) {
          e.lastMin = e.min_stock ?? e.lastMin;
          e.min_stock = null;
        } else e.min_stock = e.lastMin ?? 1;
      } else e[f] = t.value;
      e.dirty = true;
      if (f === "icon" && !t.value.trim()) return;
      if (f === "unit" || f === "nomin") this._renderItemLive();
      if (f !== "unit" && f !== "name") this._renderEditFields();
      if (f === "name") this.$.dialog.querySelector(".sheet-head h2").textContent = t.value;
    } else if (this._sheet === "settings" && t.dataset.setting && type === "change") {
      this._setting(t.dataset.setting, t.checked);
    }
  }

  _sheetAction(action, el) {
    const d = this.$.dialog;
    const e = this._edit;
    switch (action) {
      case "close":
        d.close();
        break;
      case "noop":
        break;
      case "dec":
      case "inc":
        this._adjust(e.id, action === "inc" ? 1 : -1);
        break;
      case "empty":
        this._empty(e.id);
        break;
      case "to-cesta":
        this._toCesta(e.id);
        break;
      case "min-dec":
      case "min-inc":
        e.min_stock = Math.max(0, (e.min_stock ?? 0) + (action === "min-inc" ? 1 : -1));
        e.lastMin = e.min_stock;
        e.dirty = true;
        this._renderEditFields();
        this._renderItemLive();
        break;
      case "pack-dec":
      case "pack-inc":
        e.pack = Math.max(1, e.pack + (action === "pack-inc" ? 1 : -1));
        e.dirty = true;
        this._renderEditFields();
        break;
      case "emojis":
        d.querySelector(".emoji-grid").hidden = !d.querySelector(".emoji-grid").hidden;
        break;
      case "pick":
        e.icon = el.dataset.emoji;
        e.dirty = true;
        d.querySelector(".emoji-grid").hidden = true;
        this._renderEditFields();
        break;
      case "pick-dept":
        e.department = el.dataset.id;
        e.dirty = true;
        this._renderEditFields();
        break;
      case "ask-delete":
        this._openDelete();
        break;
      case "back":
        this._openItem(e.id);
        break;
      case "delete":
      case "delete-ignore":
        this._sheet = null;
        d.close();
        this._delete(e.id, action === "delete-ignore");
        break;
      case "dmin-dec":
      case "dmin-inc": {
        const cur = this._state.settings.default_min;
        let next;
        if (action === "dmin-inc") next = cur === null ? 0 : Math.min(99, cur + 1);
        else next = cur === null || cur <= 0 ? cur : cur - 1;
        this._setting("default_min", next);
        break;
      }
      case "unignore":
        this._optimistic((st) => (st.ignored = st.ignored.filter((n) => n !== el.dataset.name)));
        this._ws({ type: "despensa/ignored/remove", name: el.dataset.name });
        this._renderSettings();
        break;
    }
  }

}

/* --------------------------------------------------------- panel lateral */
class DespensaPanel extends DespensaBase {
  get mode() {
    return "panel";
  }
  set panel(p) {
    this._panel = p;
  }
  set route(r) {
    this._route = r;
  }
}

/* --------------------------------------------------------------- tarjeta */
class DespensaCard extends DespensaBase {
  get mode() {
    return "card";
  }
  setConfig(config) {
    this._config = { ...(config || {}) };
    if (this._config.filter === "low") this._filter = "low";
    if (this.$) {
      this.shadowRoot.querySelector(".title").textContent = this._config.title || "Despensa";
      this._render();
    }
  }
  getCardSize() {
    return 8;
  }
  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
  }
  static getStubConfig() {
    return {};
  }
}

if (!customElements.get("despensa-panel")) customElements.define("despensa-panel", DespensaPanel);
if (!customElements.get("despensa-card")) {
  customElements.define("despensa-card", DespensaCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "despensa-card",
    name: "Despensa",
    description: "Armario con lo que hay en casa: stock por producto, aviso al llegar al mínimo y enlace con Cesta.",
  });
  console.info(`%c DESPENSA %c ${DESPENSA_VERSION} `, "background:#8a5a35;color:#fff;border-radius:4px 0 0 4px;padding:2px 4px", "background:#555;color:#fff;border-radius:0 4px 4px 0;padding:2px 4px");
}
