/* Backend simulado para la vista previa: replica en JS el gestor de Python
 * (custom_components/despensa/manager.py), el puente con Cesta y las frases de voz,
 * y expone un objeto `hass` falso con callWS y connection.subscribeMessage. Solo para la demo. */
(function () {
  const CATALOG = window.DESPENSA_CATALOG;
  const DEPARTMENTS = window.DESPENSA_DEPARTMENTS;

  const norm = (s) => String(s ?? "").normalize("NFKD").replace(/[̀-ͯ]/g, "").trim().toLowerCase().replace(/\s+/g, " ");
  const stem = (w) => {
    if (w.length > 3 && w.endsWith("s")) w = w.slice(0, -1);
    if (w.length > 3 && w.endsWith("e")) w = w.slice(0, -1);
    return w;
  };
  const stems = (t) => norm(t).split(/[^a-z0-9]+/).filter(Boolean).map(stem);
  const clean = (n) => {
    n = String(n ?? "").replace(/\s+/g, " ").trim();
    return n ? n[0].toUpperCase() + n.slice(1) : n;
  };
  const uid = () => Math.random().toString(16).slice(2, 14);
  const now = () => Math.round(Date.now()) / 1000;
  const err = (code, message, candidates = []) => Object.assign(new Error(message), { code, candidates });
  const isLow = (i) => i.min_stock !== null && i.stock <= i.min_stock;
  const clamp = (n) => Math.max(0, Math.min(9999, Math.round(Number(n) || 0)));
  const contains = (hay, needle) => hay.some((_, i) => needle.every((w, j) => hay[i + j] === w));

  const catIndex = new Map(CATALOG.map((e) => [norm(e.name), e]));
  const catStems = CATALOG.map((e) => [stems(e.name), e]);
  const byStems = new Map(catStems.map(([w, e]) => [w.join(" "), e]));
  const canonical = (name) => catIndex.get(norm(name)) || byStems.get(stems(name).join(" "));
  function guess(name) {
    const key = norm(name);
    if (catIndex.has(key)) return catIndex.get(key);
    const words = stems(name);
    let best = null;
    let bestScore = 0;
    for (const [cw, entry] of catStems) {
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

  /* ---------- datos de ejemplo */
  function seed() {
    const t = now();
    const H = 3600;
    const D = 86400;
    const spec = [
      // nombre, stock, mínimo, unidad, unidades por compra
      ["Tomates", 4, 2, "", 1], ["Patatas", 3, 1, "kg", 1], ["Cebollas", 1, 2, "", 1], ["Ajos", 2, 0, "cabezas", 1],
      ["Plátanos", 0, 0, "", 1],
      ["Pan de molde", 1, 0, "", 1],
      ["Leche", 3, 2, "bricks", 6], ["Huevos", 10, 4, "", 12], ["Yogur griego", 2, 2, "", 4], ["Mantequilla", 1, 0, "", 1],
      ["Arroz", 2, 1, "paquetes", 1], ["Pasta", 4, 2, "paquetes", 1], ["Lentejas", 1, 1, "botes", 1],
      ["Atún en lata", 6, 3, "latas", 3], ["Tomate frito", 3, 1, "botes", 1], ["Aceite de oliva", 1, 1, "botellas", 1],
      ["Café molido", 0, 1, "paquetes", 1], ["Galletas", 2, 1, "paquetes", 1], ["Cereales", 1, 0, "cajas", 1],
      ["Agua con gas", 8, 4, "botellas", 6], ["Cerveza", 11, 6, "latas", 12],
      ["Detergente", 1, 1, "", 1], ["Papel de cocina", 3, 2, "rollos", 2], ["Bolsas de basura", 1, 0, "rollos", 1],
      ["Papel higiénico", 9, 4, "rollos", 12], ["Pasta de dientes", 1, 1, "", 1],
    ];
    const items = spec.map(([name, stock, min, unit, pack]) => {
      const e = catIndex.get(norm(name));
      return {
        id: uid(), name: e.name, icon: e.icon, department: e.department, stock, min_stock: min, unit, pack,
        created_at: t - 40 * D, updated_at: t - D,
      };
    });
    const by = (n) => items.find((i) => norm(i.name) === norm(n));
    const logSpec = [
      ["Leche", -1, "used", "voz", 0.4 * H],
      ["Café molido", -1, "empty", "voz", 3 * H],
      ["Atún en lata", -2, "used", "voz", 20 * H],
      ["Huevos", 12, "purchased", "cesta", 1.2 * D],
      ["Agua con gas", 6, "purchased", "cesta", 1.2 * D],
      ["Cebollas", -2, "used", "panel", 1.6 * D],
      ["Plátanos", -3, "used", "panel", 2.1 * D],
      ["Papel higiénico", 12, "purchased", "cesta", 4 * D],
    ];
    const log = logSpec.map(([name, delta, kind, source, agoS]) => {
      const it = by(name);
      return { id: uid(), ts: t - agoS, item_id: it.id, name: it.name, icon: it.icon, department: it.department, delta, stock: it.stock, kind, source, created: false };
    });
    const cestaItems = ["Plátanos", "Café molido"].map((n) => {
      const e = catIndex.get(norm(n));
      return { id: uid(), name: e.name, icon: e.icon, department: e.department, note: "" };
    });
    cestaItems.push({ id: uid(), name: "Fresas", icon: "🍓", department: "fruta_verdura", note: "" });
    cestaItems.push({ id: uid(), name: "Leche", icon: "🥛", department: "lacteos", note: "6 uds" });
    return {
      items,
      log,
      settings: { default_min: 0, add_from_cesta: true, auto_cesta: false, voice: true },
      ignored: {},
      cesta: { items: cestaItems, departments: structuredClone(DEPARTMENTS) },
    };
  }

  /* ---------- operaciones (mismas reglas que manager.py) */
  class Backend {
    constructor() {
      this.listeners = new Set();
      this.cestaListeners = new Set();
      this.data = seed();
      this.deleted = [];
    }
    reset() {
      this.data = seed();
      this.emit();
    }
    snapshot() {
      return {
        items: structuredClone(this.data.items),
        log: structuredClone(this.data.log),
        settings: { ...this.data.settings },
        ignored: Object.values(this.data.ignored).sort(),
        departments: structuredClone(this.data.cesta.departments),
        cesta: { available: true, in_list: this.data.cesta.items.map((i) => norm(i.name)).sort() },
        voice_active: this.data.settings.voice,
      };
    }
    emit() {
      const snap = this.snapshot();
      for (const l of this.listeners) l(structuredClone(snap));
      for (const l of this.cestaListeners) l(structuredClone(this.data.cesta.items));
    }
    get items() { return this.data.items; }
    get log() { return this.data.log; }
    deptIds() { return this.data.cesta.departments.map((d) => d.id); }
    fallback() { const ids = this.deptIds(); return ids.includes("otros") ? "otros" : ids[ids.length - 1]; }
    resolveDept(v) {
      if (!v) return null;
      const d = this.data.cesta.departments.find((x) => x.id === v || norm(x.name) === norm(v));
      return d ? d.id : null;
    }
    get(id) {
      const it = this.items.find((i) => i.id === id);
      if (!it) throw err("not_found", `No hay ningún producto con id ${id}`);
      return it;
    }
    findByName(name) {
      const k = norm(name);
      if (!k) return null;
      const s = stems(name).join(" ");
      return this.items.find((i) => norm(i.name) === k) || this.items.find((i) => stems(i.name).join(" ") === s) || null;
    }
    find(text) {
      let it = this.findByName(text);
      if (it) return it;
      const canon = canonical(text);
      if (canon && (it = this.findByName(canon.name))) return it;
      const words = stems(text);
      if (!words.length) throw err("not_found", "No has dicho qué producto");
      let wider = this.items.filter((i) => contains(stems(i.name), words));
      if (wider.length > 1) {
        const inStock = wider.filter((i) => i.stock > 0);
        if (inStock.length === 1) wider = inStock;
      }
      if (wider.length === 1) return wider[0];
      if (wider.length > 1) {
        const names = wider.map((i) => i.name).sort((a, b) => a.localeCompare(b, "es"));
        throw err("ambiguous", `Hay varios productos: ${names.join(", ")}`, names);
      }
      const narrower = this.items.filter((i) => contains(words, stems(i.name)));
      if (narrower.length) return narrower.sort((a, b) => stems(b.name).length - stems(a.name).length)[0];
      throw err("not_found", `«${clean(text)}» no está en la despensa`);
    }
    addLog(item, delta, kind, source, created = false) {
      const t = now();
      const last = this.log[0];
      if (last && source === "panel" && !created && !last.created && last.item_id === item.id && last.source === source && last.kind === kind && t - last.ts <= 90) {
        last.delta += delta;
        last.stock = item.stock;
        last.ts = t;
        if (last.delta === 0 && kind !== "set") {
          this.log.shift();
          return { ...last, id: null };
        }
        return last;
      }
      const entry = { id: uid(), ts: t, item_id: item.id, name: item.name, icon: item.icon, department: item.department, delta, stock: item.stock, kind, source, created };
      this.log.unshift(entry);
      this.data.log = this.log.slice(0, 120);
      return entry;
    }
    stockChanged(item, wasLow) {
      if (!wasLow && isLow(item) && this.data.settings.auto_cesta) this.cestaAdd(item);
    }
    create({ name, stock, icon, department, min_stock, unit, pack, source = "panel", kind = "added" }) {
      name = clean(name);
      if (!name) throw err("invalid_name", "El nombre no puede estar vacío");
      const amount = stock == null ? 1 : clamp(stock);
      const existing = this.findByName(name);
      if (existing) return { item: existing, log: amount ? this.adjust({ item_id: existing.id, delta: amount, kind, source }).log : null };
      const canon = canonical(name);
      if (canon) name = canon.name;
      const g = guess(name);
      let dept = this.resolveDept(department) || (g && g.department);
      if (!this.deptIds().includes(dept)) dept = this.fallback();
      const item = {
        id: uid(), name, icon: (icon || "").trim() || (g ? g.icon : "🛒"), department: dept, stock: amount,
        min_stock: min_stock === undefined ? this.data.settings.default_min : min_stock, unit: unit || "", pack: pack || 1,
        created_at: now(), updated_at: now(),
      };
      this.items.push(item);
      delete this.data.ignored[norm(name)];
      const entry = this.addLog(item, amount, kind, source, true);
      this.stockChanged(item, false);
      return { item, log: entry, low: isLow(item) };
    }
    adjust({ item_id, delta, kind, source = "panel" }) {
      const item = this.get(item_id);
      const wasLow = isLow(item);
      const before = item.stock;
      item.stock = clamp(before + delta);
      const real = item.stock - before;
      const entry = this.addLog(item, real, kind || (real >= 0 ? "added" : "used"), source);
      this.stockChanged(item, wasLow);
      return { item, log: entry, low: isLow(item) };
    }
    setStock(item_id, stock, kind = "set", source = "panel") {
      const item = this.get(item_id);
      const wasLow = isLow(item);
      const before = item.stock;
      item.stock = clamp(stock);
      const entry = this.addLog(item, item.stock - before, kind, source);
      this.stockChanged(item, wasLow);
      return { item, log: entry, low: isLow(item) };
    }
    update({ item_id, ...ch }) {
      const item = this.get(item_id);
      if (ch.name != null) {
        const n = clean(ch.name);
        if (!n) throw err("invalid_name", "El nombre no puede estar vacío");
        const other = this.findByName(n);
        if (other && other !== item) throw err("duplicate", `Ya tienes «${other.name}» en la despensa`);
        item.name = n;
      }
      if (ch.icon) item.icon = ch.icon.trim();
      if (ch.department != null) item.department = this.resolveDept(ch.department) || this.fallback();
      if ("min_stock" in ch) item.min_stock = ch.min_stock;
      if (ch.unit != null) item.unit = ch.unit.trim();
      if (ch.pack != null) item.pack = Math.max(1, ch.pack);
      return { item, log: null, low: isLow(item) };
    }
    remove({ item_id, ignore }) {
      const item = this.get(item_id);
      this.data.items = this.items.filter((i) => i !== item);
      const key = norm(item.name);
      const fresh = ignore && !this.data.ignored[key];
      if (ignore) this.data.ignored[key] = item.name;
      this.deleted.unshift([item, fresh]);
      return item;
    }
    restore({ item_id }) {
      const i = this.deleted.findIndex(([it]) => it.id === item_id);
      if (i < 0) throw err("not_found", "Ya no se puede recuperar");
      const [[item, fresh]] = this.deleted.splice(i, 1);
      if (!this.findByName(item.name)) this.items.push(item);
      if (fresh) delete this.data.ignored[norm(item.name)];
      return item;
    }
    undo({ log_id }) {
      const entry = this.log.find((e) => e.id === log_id);
      if (!entry) throw err("not_found", "Ese movimiento ya no existe");
      this.data.log = this.log.filter((e) => e !== entry);
      const item = this.items.find((i) => i.id === entry.item_id);
      if (!item) return null;
      if (entry.created && !this.log.some((e) => e.item_id === item.id)) {
        this.data.items = this.items.filter((i) => i !== item);
        return null;
      }
      item.stock = clamp(item.stock - entry.delta);
      return item;
    }
    settingsSet(msg) {
      for (const k of ["default_min", "add_from_cesta", "auto_cesta", "voice"]) if (k in msg) this.data.settings[k] = msg[k];
    }

    /* ---------- Cesta simulada */
    inCesta(item) {
      return this.data.cesta.items.some((c) => norm(c.name) === norm(item.name));
    }
    cestaAdd(item) {
      if (this.inCesta(item)) return false;
      this.data.cesta.items.push({ id: uid(), name: item.name, icon: item.icon, department: item.department, note: "" });
      return true;
    }
    cestaAddLow() {
      const low = this.items.filter(isLow).sort((a, b) => this.deptIds().indexOf(a.department) - this.deptIds().indexOf(b.department));
      return low.filter((i) => this.cestaAdd(i)).map((i) => i.name);
    }
    cestaAddByName(name) {
      name = clean(name);
      if (!name) return;
      const canon = canonical(name);
      const g = guess(name);
      const it = { name: canon ? canon.name : name, icon: g ? g.icon : "🛒", department: g ? g.department : "otros" };
      this.cestaAdd(it);
      this.emit();
    }
    /* "Comprado" en Cesta → el puente suma en la despensa */
    cestaPurchase(id) {
      const entry = this.data.cesta.items.find((c) => c.id === id);
      if (!entry) return;
      this.data.cesta.items = this.data.cesta.items.filter((c) => c !== entry);
      const key = norm(entry.name);
      if (!this.data.ignored[key]) {
        const m = /^(?:pack de |x ?)?(\d{1,3}) ?(?:x|u|uds?\.?|unidades?|latas?|botes?|bricks?|botellas?|paquetes?)?$/.exec(norm(entry.note));
        const amount = m ? Number(m[1]) : null;
        const item = this.findByName(entry.name);
        if (item) this.adjust({ item_id: item.id, delta: amount || item.pack || 1, kind: "purchased", source: "cesta" });
        else if (this.data.settings.add_from_cesta)
          this.create({ name: entry.name, stock: amount || 1, icon: entry.icon, department: entry.department, source: "cesta", kind: "purchased" });
      }
      this.emit();
    }
    subscribeCesta(cb) {
      this.cestaListeners.add(cb);
      cb(structuredClone(this.data.cesta.items));
    }

    call(msg) {
      const ops = {
        "despensa/catalog": () => ({ catalog: CATALOG }),
        "despensa/item/create": () => this.create(msg),
        "despensa/item/adjust": () => this.adjust(msg),
        "despensa/item/update": () => this.update(msg),
        "despensa/item/empty": () => this.setStock(msg.item_id, 0, "empty"),
        "despensa/item/delete": () => this.remove(msg),
        "despensa/item/restore": () => this.restore(msg),
        "despensa/log/undo": () => this.undo(msg),
        "despensa/log/clear": () => (this.data.log = []) && null,
        "despensa/cesta/add": () => ({ added: this.cestaAdd(this.get(msg.item_id)) }),
        "despensa/cesta/add_low": () => ({ added: this.cestaAddLow() }),
        "despensa/settings/set": () => this.settingsSet(msg),
        "despensa/ignored/remove": () => delete this.data.ignored[norm(msg.name)] && null,
      };
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          const op = ops[msg.type];
          if (!op) return reject(err("unknown_command", "Unknown command."));
          try {
            const result = op();
            if (msg.type !== "despensa/catalog") this.emit();
            resolve(result === undefined ? null : structuredClone(result));
          } catch (e) {
            reject(e);
          }
        }, 60);
      });
    }
    subscribe(cb) {
      this.listeners.add(cb);
      setTimeout(() => cb(this.snapshot()), 30);
      return Promise.resolve(() => this.listeners.delete(cb));
    }

    /* ---------- voz (las mismas frases y respuestas que voice.py, simplificadas) */
    say(text) {
      const orig = String(text).replace(/[¿?¡!.,;:]/g, " ").split(/\s+/).filter(Boolean);
      const t = orig.map(norm).join(" ");
      const R = [
        ["use", /^(?:apunta que )?(?:he|hemos) (?:usado|gastado|consumido|cogido|abierto|tomado|utilizado|sacado) (.+)$/],
        ["use", /^(?:use|gaste|consumi|cogi|abri|utilice|saque) (.+)$/],
        ["use", /^(?:resta|quita|descuenta|saca) (.+) de la despensa$/],
        ["empty", /^se (?:ha|han) (?:acabado|terminado|agotado) (.+)$/],
        ["empty", /^se (?:acabo|acabaron|termino|terminaron|agoto|agotaron) (.+)$/],
        ["empty", /^(.+) se (?:ha|han) (?:acabado|terminado|agotado)$/],
        ["empty", /^(?:he|hemos) (?:acabado|terminado|vaciado) (.+)$/],
        ["add", /^(?:he|hemos) (?:comprado|repuesto|traido) (.+)$/],
        ["add", /^(?:compre|traje|repuse|compramos) (.+)$/],
        ["add", /^(?:anade|anadir|mete|guarda|suma|pon) (.+) (?:a|en) la despensa$/],
        ["cesta", /^(?:anade|pon|mete|apunta|pasa|manda) (?:a la cesta )?(?:todo )?lo que (?:falta|se esta acabando|hay que reponer|hay que comprar)(?: (?:a|en) la (?:cesta|lista de la compra|compra))?$/],
        ["stock", /^(?:cuanto|cuanta|cuantos|cuantas) (.+?) (?:queda|quedan|tengo|tenemos|me queda|me quedan|nos queda|nos quedan)(?: en (?:la despensa|casa))?$/],
        ["stock", /^(?:cuanto|cuanta|cuantos|cuantas) (.+?) hay en la despensa$/],
        ["stock", /^(?:queda|quedan|hay) (.+) en la despensa$/],
        ["stock", /^(?:me|nos) (?:queda|quedan) (.+)$/],
        ["low", /^que (?:falta|hace falta|tengo que comprar|hay que comprar|tenemos que comprar|necesito comprar|hay que reponer|se esta acabando|hay por reponer)(?: en (?:la despensa|casa))?$/],
      ];
      if (!this.data.settings.voice) return "Lo siento, no lo he entendido. (Las frases de Despensa están desactivadas en los ajustes.)";
      for (const [kind, re] of R) {
        const m = new RegExp(re.source, "d").exec(t);
        if (!m) continue;
        let raw = "";
        if (m[1]) {
          // mismas palabras, pero con tildes y mayúsculas como se dijeron
          const start = t.slice(0, m.indices[1][0]).split(" ").filter(Boolean).length;
          raw = orig.slice(start, start + m[1].split(" ").length).join(" ");
        }
        try {
          const out = this.voice(kind, raw);
          this.emit();
          return out;
        } catch (e) {
          if (e.code === "ambiguous") return `¿Cuál? En la despensa tengo ${join(e.candidates)}.`;
          return `${e.message}.`;
        }
      }
      return "Lo siento, no lo he entendido. Prueba con «He usado dos latas de atún» o «¿Qué falta?».";
    }
    voice(kind, rawText) {
      const lname = (it) => it.name[0].toLowerCase() + it.name.slice(1);
      const unitFor = (u, n) => (n === 1 && u.endsWith("s") ? (/[dlnzj]es$/.test(u) ? u.slice(0, -2) : u.slice(0, -1)) : u);
      const describe = (it) => {
        if (it.stock <= 0) return `No queda nada de ${lname(it)}.`;
        const verb = it.stock === 1 ? "queda" : "quedan";
        if (!it.unit) return `De ${lname(it)} te ${verb} ${it.stock}.`;
        // "Atún en lata" contado en latas → "4 latas de atún"
        let nm = lname(it);
        const key = norm(nm);
        for (const u of new Set([norm(it.unit), singular(norm(it.unit))])) {
          if (key.endsWith(` en ${u}`) && key.length > u.length + 4) nm = nm.slice(0, -u.length - 4);
          else if (key.startsWith(`${u} de `) && key.length > u.length + 4) nm = nm.slice(u.length + 4);
        }
        return `Te ${verb} ${it.stock} ${unitFor(it.unit, it.stock)} de ${nm}.`;
      };
      if (kind === "low") {
        const low = this.items.filter(isLow).sort((a, b) => this.deptIds().indexOf(a.department) - this.deptIds().indexOf(b.department));
        if (!low.length) return "No falta nada: todo está por encima del mínimo.";
        let s = `Hay que reponer ${join(low.map((i) => i.name))}.`;
        const inC = low.filter((i) => this.inCesta(i));
        if (inC.length === low.length) s += " Ya está todo en la Cesta.";
        else if (inC.length) s += ` Ya están en la Cesta: ${join(inC.map((i) => i.name))}.`;
        return s;
      }
      if (kind === "cesta") {
        if (!this.items.some(isLow)) return "No hay nada por reponer.";
        const added = this.cestaAddLow();
        if (!added.length) return "Ya estaba todo en la Cesta.";
        return `He añadido ${added.length} ${added.length === 1 ? "producto" : "productos"} a la Cesta: ${join(added)}.`;
      }
      const { quantity, all, candidates } = parseSpoken(rawText);
      if (!candidates.length) throw err("not_found", "No he entendido qué producto");
      const resolve = () => {
        let first = null;
        for (const c of candidates) {
          try {
            return this.find(c);
          } catch (e) {
            if (e.code === "ambiguous") throw e;
            first = first || e;
          }
        }
        throw first;
      };
      if (kind === "stock") {
        const it = resolve();
        let s = describe(it);
        if (isLow(it)) s += this.inCesta(it) ? " Ya está en la Cesta." : it.stock > 0 ? " Está en el mínimo." : "";
        return s;
      }
      if (kind === "add") {
        try {
          const it = resolve();
          this.adjust({ item_id: it.id, delta: quantity || it.pack || 1, source: "voz" });
          return "Hecho. " + describe(it);
        } catch (e) {
          if (e.code !== "not_found") throw e;
        }
        const { item } = this.create({ name: candidates[candidates.length - 1], stock: quantity || 1, source: "voz" });
        return `He añadido ${lname(item)} a la despensa. ` + describe(item);
      }
      const it = resolve();
      const wasLow = isLow(it);
      const inCesta = this.inCesta(it);
      const before = it.stock;
      let s;
      if (kind === "empty" || all) {
        this.setStock(it.id, 0, "empty", "voz");
        s = `Apuntado: no queda nada de ${lname(it)}.`;
      } else {
        this.adjust({ item_id: it.id, delta: -(quantity || 1), kind: "used", source: "voz" });
        s = before <= 0 ? `Según la despensa ya no quedaba ${lname(it)}; lo dejo a cero.` : "Hecho. " + describe(it);
      }
      if (!wasLow && isLow(it)) {
        const empty = it.stock <= 0;
        if (inCesta) s += empty ? " Ya está en la Cesta." : " Ya estás en el mínimo y ya está en la Cesta.";
        else if (this.data.settings.auto_cesta) s += empty ? " Lo añado a la Cesta." : " Ya estás en el mínimo: lo añado a la Cesta.";
        else if (!empty) s += " Ya estás en el mínimo.";
      }
      return s;
    }
  }

  const NUMBERS = { un: 1, uno: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7, ocho: 8, nueve: 9, diez: 10, once: 11, doce: 12, quince: 15, veinte: 20 };
  const ARTICLES = new Set("el la los las lo unos unas del al mi mis nuestro nuestra otro otra ultimo ultima poco algo de".split(" "));
  const CONTAINERS = new Set("lata bote brick botella paquete caja bolsa rollo pieza sobre tarro pack unidad ud kilo kg litro tableta barra docena carton envase tarrina bandeja capsula frasco tubo".split(" "));
  const singular = (w) => (/[dlnzj]es$/.test(w) && w.length > 4 ? w.slice(0, -2) : w.endsWith("s") ? w.slice(0, -1) : w);
  function parseSpoken(text) {
    let raw = String(text).replace(/[¿?¡!.,;:]/g, " ").split(/\s+/).filter(Boolean);
    let words = raw.map(norm);
    for (const tail of [["de", "la", "despensa"], ["en", "la", "despensa"], ["en", "casa"], ["por", "favor"], ["me"], ["nos"]]) {
      if (words.length > tail.length && tail.every((w, i) => words[words.length - tail.length + i] === w)) {
        raw = raw.slice(0, -tail.length);
        words = words.slice(0, -tail.length);
      }
    }
    let quantity = null;
    let all = false;
    let i = 0;
    for (; i < words.length; i++) {
      const w = words[i];
      if (/^\d+$/.test(w)) quantity = Number(w);
      else if (w === "media" && words[i + 1] === "docena") (quantity = 6), i++;
      else if (w === "docena") quantity = 12 * (quantity || 1);
      else if (w === "par" && (quantity === null || quantity === 1)) quantity = 2;
      else if (w in NUMBERS && quantity === null) quantity = NUMBERS[w];
      else if (["todo", "toda", "todos", "todas"].includes(w)) all = true;
      else if (!ARTICLES.has(w)) break;
    }
    raw = raw.slice(i);
    words = words.slice(i);
    const candidates = [];
    if (raw.length) {
      candidates.push(raw.join(" "));
      if (raw.length > 2 && (CONTAINERS.has(words[0]) || CONTAINERS.has(singular(words[0]))) && words[1] === "de") candidates.push(raw.slice(2).join(" "));
    }
    return { quantity, all, candidates };
  }
  const join = (names) => {
    names = names.map((n) => n[0].toLowerCase() + n.slice(1));
    return names.length <= 1 ? names.join("") : `${names.slice(0, -1).join(", ")} y ${names[names.length - 1]}`;
  };

  const backend = new Backend();
  window.DespensaDemo = {
    backend,
    hass: {
      language: "es",
      dockedSidebar: "docked",
      callWS: (msg) => backend.call(msg),
      connection: { subscribeMessage: (cb) => backend.subscribe(cb) },
    },
  };
})();
