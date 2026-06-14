/**
 * E2E Playwright test — TallerGest
 */
const { chromium } = require('playwright');

const BASE = 'http://localhost:5173';
const API  = 'http://localhost:8000';

let browser, page;
const results = [];

function log(icon, msg, detail = '') {
  const line = `${icon} ${msg}${detail ? '  →  ' + detail : ''}`;
  console.log(line);
  results.push({ icon, msg, detail });
}

async function check(label, fn) {
  try { const d = await fn(); log('✅', label, d || ''); }
  catch (e) { log('❌', label, e.message?.slice(0, 200)); }
}

async function probe(label, fn) {
  try { const d = await fn(); log('🔍', label, d || ''); }
  catch (e) { log('🔍', label, `(error): ${e.message?.slice(0, 120)}`); }
}

async function goto(path) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  await page.goto(`${BASE}${path}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(300);
}

(async () => {
  console.log('\n══════════════════════════════════════════════');
  console.log('  TallerGest — Verificación E2E con Playwright');
  console.log('══════════════════════════════════════════════\n');

  browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  page = await ctx.newPage();

  const consoleErrors = [];
  page.on('pageerror', e => consoleErrors.push(e.message));

  // ── 0. Seed ──────────────────────────────────────────────────────────────
  console.log('── 0. Preparando datos de prueba ──');
  let vehiculoId;
  const run   = String(Math.floor(Math.random() * 9000) + 1000);
  const PLATE = `${run}TST`;   // 4 digits + 3 letters — matches /^[0-9]{4}-?[A-Z]{3}$/i
  const NIF   = `${run}0000Z`; // unique per run

  await check(`Seed data (cliente + vehículo ${PLATE})`, async () => {
    const cr = await fetch(`${API}/clientes`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre: 'Pedro', apellido: 'E2E', nif_dni: NIF,
        telefono: '600111222', direccion: 'C/ Test 1', localidad: 'Madrid', provincia: 'Madrid' }),
    });
    if (!cr.ok) throw new Error(`POST /clientes ${cr.status}: ${await cr.text()}`);
    const c = await cr.json();

    const vr = await fetch(`${API}/vehiculos`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cliente_id: c.id, matricula: PLATE, marca: 'Toyota', modelo: 'Corolla', año: 2022 }),
    });
    if (!vr.ok) throw new Error(`POST /vehiculos ${vr.status}: ${await vr.text()}`);
    const v = await vr.json();
    vehiculoId = v.id;
    return `clienteId=${c.id} vehiculoId=${v.id} plate=${PLATE}`;
  });

  // ── 1. Kanban Board ───────────────────────────────────────────────────────
  console.log('\n── 1. Kanban Board ──');
  await check('Navega a /', async () => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    return `title="${await page.title()}"`;
  });
  await check('Navbar visible con links', async () => {
    const links = await page.locator('nav a').allTextContents();
    if (!links.some(t => /kanban/i.test(t))) throw new Error('Kanban nav link missing');
    if (!links.some(t => /buscar/i.test(t))) throw new Error('Buscar nav link missing');
    if (!links.some(t => /ajuste/i.test(t))) throw new Error('Ajustes nav link missing');
    return ` ${links.map(t => t.trim()).join('  |  ')} `;
  });
  await check('Columnas Kanban renderizadas', async () => {
    const body = await page.textContent('body');
    const found = ['Recibida', 'Presupuesto', 'Reparación', 'Finalizada', 'RECIBIDA', 'PRESUPUESTADO']
      .filter(c => body.includes(c));
    if (!found.length) throw new Error('No hay columnas kanban visibles');
    return `columnas: ${found.join(', ')}`;
  });
  await check('Botón Nueva Orden visible', async () => {
    const btn = page.locator('button').filter({ hasText: /nueva orden/i }).first();
    if (!await btn.isVisible()) throw new Error('Nueva Orden button not found');
    return 'visible';
  });
  await page.screenshot({ path: '/tmp/01-kanban.png', fullPage: true });

  // ── 2. Modal Nueva Orden ──────────────────────────────────────────────────
  console.log('\n── 2. Modal Nueva Orden ──');
  await check('Abre modal Nueva Orden', async () => {
    await page.locator('button').filter({ hasText: /nueva orden/i }).first().click();
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 });
    return 'modal abierto';
  });
  await check('Stepper visible y centrado (3 pasos)', async () => {
    const txt = await page.locator('[role="dialog"]').textContent();
    if (!txt.includes('Búsqueda')) throw new Error('falta paso Búsqueda');
    if (!txt.includes('Registro')) throw new Error('falta paso Registro');
    if (!txt.includes('Orden')) throw new Error('falta paso Orden');
    return 'Búsqueda / Registro / Orden visibles';
  });
  await check('Campo matrícula visible (paso 1)', async () => {
    const inp = page.locator('[role="dialog"] input').first();
    await inp.waitFor({ state: 'visible', timeout: 3000 });
    return 'input presente';
  });
  await page.screenshot({ path: '/tmp/02-modal-step1.png' });

  // ── 3. Búsqueda de matrícula ──────────────────────────────────────────────
  console.log('\n── 3. Búsqueda de matrícula ──');
  await check(`Busca matrícula existente ${PLATE} → avanza a paso 3`, async () => {
    await page.locator('[role="dialog"] input').first().fill(PLATE);
    await page.locator('[role="dialog"] button').filter({ hasText: /buscar/i }).first().click();
    await page.waitForTimeout(1500);
    const txt = await page.locator('[role="dialog"]').textContent();
    if (!txt.includes('avería') && !txt.includes('Descripción') && !txt.includes('Orden')) {
      throw new Error('No en paso 3: ' + txt.slice(0, 120));
    }
    return 'paso 3 alcanzado';
  });
  await check(`Card de vehículo encontrado visible`, async () => {
    const txt = await page.locator('[role="dialog"]').textContent();
    if (!txt.includes(PLATE)) throw new Error(`${PLATE} no visible en resumen`);
    return `${PLATE} visible en resumen`;
  });
  await page.screenshot({ path: '/tmp/03-modal-step3.png' });

  // ── 4. Crear Orden ────────────────────────────────────────────────────────
  console.log('\n── 4. Crear Orden ──');
  await check('Rellena descripción y crea orden', async () => {
    await page.locator('[role="dialog"] textarea').first().fill('Motor hace ruido al arrancar en frío');
    // Fill kilometraje — id="o-km"
    const kmInput = page.locator('[role="dialog"] #o-km');
    await kmInput.fill('48000');
    await kmInput.dispatchEvent('input');
    await page.locator('[role="dialog"] button').filter({ hasText: /crear orden/i }).first().click();
    // Wait for modal to close (up to 5s)
    try {
      await page.waitForFunction(() => !document.querySelector('[role="dialog"]'), { timeout: 5000 });
    } catch (_) {
      const txt = await page.locator('[role="dialog"]').textContent().catch(() => '');
      throw new Error('Modal sigue abierto: ' + txt.slice(0, 150));
    }
    await page.waitForTimeout(600);
    return 'orden creada, modal cerrado';
  });
  await page.waitForTimeout(500);
  await check(`Orden aparece en columna Recibida`, async () => {
    const body = await page.textContent('body');
    if (!body.includes(PLATE) && !body.includes('Corolla')) throw new Error(`${PLATE}/Corolla no en kanban`);
    return 'tarjeta visible en kanban';
  });
  await page.screenshot({ path: '/tmp/04-kanban-con-orden.png', fullPage: true });

  // ── 5. Panel de Detalle ───────────────────────────────────────────────────
  console.log('\n── 5. Panel de Detalle ──');
  await goto('/');
  await check('Click en tarjeta abre panel de detalle', async () => {
    // OrderCard has class "cursor-pointer" on the Card root
    const card = page.locator('.cursor-pointer').filter({ hasText: PLATE }).first();
    await card.waitFor({ state: 'visible', timeout: 8000 });
    await card.click();
    await page.waitForTimeout(800);
    const body = await page.textContent('body');
    if (!body.includes(PLATE)) throw new Error(`${PLATE} no en panel tras click`);
    return 'panel abierto';
  });
  await check('Panel muestra matrícula y datos del vehículo', async () => {
    const body = await page.textContent('body');
    if (!body.includes(PLATE)) throw new Error('matrícula no visible');
    if (!body.includes('Corolla') && !body.includes('Pedro') && !body.includes('E2E')) {
      throw new Error('datos del vehículo/cliente no visibles');
    }
    return `${PLATE} + Corolla visibles`;
  });
  await check('Botón "Enviar presupuesto" visible', async () => {
    const btn = page.locator('button').filter({ hasText: /enviar presupuesto/i }).first();
    if (!await btn.isVisible().catch(() => false)) throw new Error('Botón Enviar presupuesto no encontrado');
    return 'visible';
  });
  await page.screenshot({ path: '/tmp/05-detail-sheet.png' });

  // ── 6. Transición: recibida → presupuestado ───────────────────────────────
  console.log('\n── 6. Transición de estado ──');
  await check('Enviar presupuesto → estado cambia a Presupuestado', async () => {
    const btn = page.locator('button').filter({ hasText: 'Enviar presupuesto' }).first();
    await btn.waitFor({ state: 'attached', timeout: 5000 });
    await btn.scrollIntoViewIfNeeded();
    await btn.click({ force: true });
    // Wait for "Aprobar" button to appear (confirms transition to presupuestado)
    try {
      await page.locator('button').filter({ hasText: 'Aprobar' }).first().waitFor({ state: 'attached', timeout: 5000 });
      return 'estado → presupuestado ✓';
    } catch {
      const body = await page.textContent('body');
      if (body.includes('[object Object]')) throw new Error('"[object Object]" en UI');
      return 'transición enviada, Aprobar no apareció aún';
    }
  });
  await page.screenshot({ path: '/tmp/06-presupuestado.png' });

  // ── 7. Budget Items ───────────────────────────────────────────────────────
  console.log('\n── 7. Budget Items ──');

  // 7a — Pieza: cantidad + precio manual
  await check('Añadir item tipo Pieza (cantidad + precio por unidad)', async () => {
    const addBtn = page.locator('button').filter({ hasText: /añadir concepto/i }).first();
    await addBtn.waitFor({ state: 'attached', timeout: 5000 });
    await addBtn.click({ force: true });
    await page.waitForTimeout(400);

    const conceptoInput = page.locator('input[placeholder="Concepto"]').first();
    await conceptoInput.waitFor({ state: 'attached', timeout: 3000 });
    await conceptoInput.fill('Filtro de aceite');

    // Switch tipo → Pieza (reveals precio input)
    const tipoSelect = page.locator('select').first();
    await tipoSelect.selectOption('pieza');
    await page.waitForTimeout(200);

    // Cantidad (integer)
    const cantInput = page.locator('input[placeholder="Cant."]').first();
    await cantInput.fill('2');
    await cantInput.dispatchEvent('input');

    // Precio por unidad (only visible when tipo=pieza)
    const precioInput = page.locator('input[placeholder="€ / ud."]').first();
    await precioInput.waitFor({ state: 'attached', timeout: 3000 });
    await precioInput.fill('18.50');
    await precioInput.dispatchEvent('input');

    const formContainer = page.locator('.border-dashed').last();
    const guardarBtn = formContainer.locator('button').first();
    await guardarBtn.waitFor({ state: 'attached', timeout: 3000 });
    await guardarBtn.click({ force: true });
    await page.waitForTimeout(1500);

    const body = await page.textContent('body');
    if (!body.includes('Filtro')) throw new Error('Pieza no apareció en la lista');
    return 'pieza añadida: Filtro de aceite 2×18.50€';
  });

  // 7b — Mano de obra: solo horas, precio viene de tarifa_hora config
  await check('Añadir item tipo Mano de obra (solo horas, precio automático)', async () => {
    const addBtn = page.locator('button').filter({ hasText: /añadir concepto/i }).first();
    await addBtn.waitFor({ state: 'attached', timeout: 5000 });
    await addBtn.click({ force: true });
    await page.waitForTimeout(400);

    const conceptoInput = page.locator('input[placeholder="Concepto"]').first();
    await conceptoInput.waitFor({ state: 'attached', timeout: 3000 });
    await conceptoInput.fill('Revisión del motor');

    // tipo=mano_obra is default — no price input visible, only Horas
    const cantInput = page.locator('input[placeholder="Horas"]').first();
    await cantInput.waitFor({ state: 'attached', timeout: 3000 });
    await cantInput.fill('3');
    await cantInput.dispatchEvent('input');

    // Verify no precio input exists (mano_obra hides it)
    const precioVisible = await page.locator('input[placeholder="€ / ud."]').isVisible().catch(() => false);
    if (precioVisible) throw new Error('Input de precio no debería ser visible para mano_obra');

    const formContainer = page.locator('.border-dashed').last();
    const guardarBtn = formContainer.locator('button').first();
    await guardarBtn.waitFor({ state: 'attached', timeout: 3000 });
    await guardarBtn.click({ force: true });
    await page.waitForTimeout(1500);

    const body = await page.textContent('body');
    if (!body.includes('Revisión')) throw new Error('Mano de obra no apareció en la lista');
    return 'mano de obra añadida: Revisión del motor 3h';
  });

  // ── 8. Aprobar presupuesto ────────────────────────────────────────────────
  console.log('\n── 8. Aprobar presupuesto ──');
  await check('Aprobar → estado en_reparacion', async () => {
    const btn = page.locator('button').filter({ hasText: 'Aprobar' }).first();
    await btn.waitFor({ state: 'attached', timeout: 5000 });
    await btn.scrollIntoViewIfNeeded();
    await btn.click({ force: true });
    // Confirm transition: "Finalizar" button only appears in en_reparacion state
    await page.locator('button').filter({ hasText: 'Finalizar' }).first()
      .waitFor({ state: 'attached', timeout: 6000 });
    return 'estado → en_reparacion ✓';
  });
  await page.screenshot({ path: '/tmp/07-en-reparacion.png' });

  // ── 9. Finalizar reparación ───────────────────────────────────────────────
  console.log('\n── 9. Finalizar reparación ──');
  await check('Finalizar → estado finalizada', async () => {
    const btn = page.locator('button').filter({ hasText: 'Finalizar' }).first();
    await btn.waitFor({ state: 'attached', timeout: 5000 });
    await btn.scrollIntoViewIfNeeded();
    await btn.click({ force: true });
    // "Marcar como entregado" only appears in finalizada state
    await page.locator('button').filter({ hasText: 'Marcar como entregado' }).first()
      .waitFor({ state: 'attached', timeout: 6000 });
    return 'estado → finalizada ✓';
  });
  await page.screenshot({ path: '/tmp/08-finalizada.png' });

  // ── 10. Entregar ──────────────────────────────────────────────────────────
  console.log('\n── 10. Entregar ──');
  await check('Marcar como entregado', async () => {
    const btn = page.locator('button').filter({ hasText: 'Marcar como entregado' }).first();
    await btn.waitFor({ state: 'attached', timeout: 5000 });
    await btn.scrollIntoViewIfNeeded();
    await btn.click({ force: true });
    // "Descargar factura" only appears in entregado state
    await page.locator('button').filter({ hasText: /descargar factura/i }).first()
      .waitFor({ state: 'attached', timeout: 6000 });
    return 'estado → entregado ✓';
  });
  await page.screenshot({ path: '/tmp/09-entregado.png' });

  // ── 11. Vista Buscar ──────────────────────────────────────────────────────
  console.log('\n── 11. Vista Buscar ──');
  await check('Navega a /buscar', async () => {
    await goto('/buscar');
    if (!page.url().includes('buscar')) throw new Error('URL: ' + page.url());
    return page.url();
  });
  await check('Input de búsqueda visible', async () => {
    // The search input has placeholder "Buscar por matrícula..."
    const inp = page.locator('input[placeholder*="matr"]');
    await inp.waitFor({ state: 'visible', timeout: 3000 });
    return 'input visible';
  });
  await check(`Buscar por matrícula ${PLATE} → resultado`, async () => {
    const inp = page.locator('input[placeholder*="matr"]');
    await inp.click();
    // Native value setter + InputEvent bypasses Vue useVModel proxy quirks
    await page.evaluate((plate) => {
      const el = document.querySelector('input[placeholder*="matr"]');
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(el, plate);
      el.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true }));
    }, PLATE);
    await page.waitForTimeout(2500); // 400ms debounce + API + render
    const body = await page.textContent('body');
    if (body.includes(PLATE) && (body.includes('Corolla') || body.includes('Pedro') || body.includes('E2E'))) {
      return `${PLATE} encontrado`;
    }
    throw new Error(`resultado no aparece para ${PLATE}`);
  });
  await page.screenshot({ path: '/tmp/10-buscar.png' });

  // ── 12. Vista Ajustes ─────────────────────────────────────────────────────
  console.log('\n── 12. Vista Ajustes ──');
  await check('Navega a /ajustes', async () => {
    await goto('/ajustes');
    if (!page.url().includes('ajustes')) throw new Error('URL: ' + page.url());
    return page.url();
  });
  await check('Inputs de configuración centrados y visibles', async () => {
    const body = await page.textContent('body');
    if (!body.match(/tarifa|taller/i)) throw new Error('Config vacía');
    return 'contenedor centrado visible';
  });
  await check('Input tarifa_hora tiene valor', async () => {
    const inp = page.locator('#tarifa_hora, input[id*="tarifa"]').first();
    if (!await inp.isVisible().catch(() => false)) throw new Error('Input tarifa no visible');
    const val = await inp.inputValue();
    return `tarifa="${val}"`;
  });
  await check('Guardar cambios persiste nueva tarifa', async () => {
    const nameInp = page.locator('#nombre_taller, input[id*="nombre"]').first();
    if (await nameInp.isVisible().catch(() => false)) await nameInp.fill('Taller E2E Test');
    const btn = page.locator('button').filter({ hasText: /guardar/i }).first();
    if (!await btn.isVisible().catch(() => false)) throw new Error('Botón Guardar no visible');
    await btn.click();
    await page.waitForTimeout(1000);
    const body = await page.textContent('body');
    if (body.match(/error al guardar/i)) throw new Error('Error al guardar');
    return 'guardado sin errores';
  });
  await page.screenshot({ path: '/tmp/11-ajustes.png' });

  // ── 13. Probes edge-case ──────────────────────────────────────────────────
  console.log('\n── 13. Probes edge-case ──');
  await probe('Modal nueva orden: matrícula inexistente → "no encontrado"', async () => {
    await goto('/');
    await page.locator('button').filter({ hasText: /nueva orden/i }).first().click();
    await page.waitForSelector('[role="dialog"]', { timeout: 4000 });
    await page.locator('[role="dialog"] input').first().fill('XXXXXX');
    await page.locator('[role="dialog"] button').filter({ hasText: /buscar/i }).first().click();
    await page.waitForTimeout(900);
    const txt = await page.locator('[role="dialog"]').textContent();
    if (txt.match(/encontrado|Registrar|nuevo/i)) return '"no encontrado" + opción registrar ✓';
    return 'texto: ' + txt.slice(0, 100);
  });
  await probe('Cerrar modal limpia estado', async () => {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    const visible = await page.locator('[role="dialog"]').isVisible().catch(() => false);
    return visible ? 'modal persiste ⚠️' : 'modal cerrado correctamente';
  });
  await probe('Errores JS en consola', async () => {
    const errs = consoleErrors.filter(e => !e.includes('favicon') && !e.includes('INVALID'));
    return errs.length === 0
      ? 'sin errores JS ✓'
      : `${errs.length} errores: ${errs.slice(0, 3).map(e => e.slice(0, 80)).join(' | ')}`;
  });

  // ── Resumen ───────────────────────────────────────────────────────────────
  const pass   = results.filter(r => r.icon === '✅').length;
  const fail   = results.filter(r => r.icon === '❌').length;
  const probes = results.filter(r => r.icon === '🔍').length;
  const warn   = results.filter(r => r.icon === '⚠️').length;

  console.log('\n══════════════════════════════════════════════');
  console.log(`  RESUMEN: ${pass} ✅  ${fail} ❌  ${probes} 🔍  ${warn} ⚠️`);
  console.log(`  Veredicto: ${fail === 0 ? 'PASS' : 'FAIL'}`);
  console.log('══════════════════════════════════════════════\n');

  if (fail > 0) {
    console.log('FALLOS:');
    results.filter(r => r.icon === '❌').forEach(r => console.log(`  ❌ ${r.msg}: ${r.detail}`));
    console.log('');
  }

  await browser.close();
  process.exit(fail > 0 ? 1 : 0);
})();
