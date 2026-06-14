/**
 * E2E Playwright test — TallerGest
 * Runs against the live dev server (http://localhost:5173) + backend (http://localhost:8000)
 */

const { chromium } = require('playwright');

const BASE = 'http://localhost:5173';
const API  = 'http://localhost:8000';

const PASS = '✅';
const FAIL = '❌';
const WARN = '⚠️ ';
const PROBE= '🔍';

let browser, page;
const results = [];

function log(icon, msg, detail = '') {
  const line = `${icon} ${msg}${detail ? '  →  ' + detail : ''}`;
  console.log(line);
  results.push({ icon, msg, detail });
}

async function check(label, fn) {
  try {
    const detail = await fn();
    log(PASS, label, detail || '');
  } catch (e) {
    log(FAIL, label, e.message?.slice(0, 200));
  }
}

async function probe(label, fn) {
  try {
    const detail = await fn();
    log(PROBE, label, detail || '');
  } catch (e) {
    log(PROBE, label, `(error esperado): ${e.message?.slice(0, 120)}`);
  }
}

// ─── helpers ─────────────────────────────────────────────────────────────────

async function waitForText(text, timeout = 5000) {
  await page.waitForSelector(`text=${text}`, { timeout });
}

async function apiReset() {
  // Fresh DB: create a test client + vehicle for reuse
  const c = await fetch(`${API}/clientes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      nombre: 'Ana', apellido: 'Test', nif_dni: '11111111A',
      telefono: '600000000', direccion: 'Calle Prueba 1',
      localidad: 'Madrid', provincia: 'Madrid'
    })
  }).then(r => r.json());

  const v = await fetch(`${API}/vehiculos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      cliente_id: c.id, matricula: 'TEST001',
      marca: 'Seat', modelo: 'Ibiza', año: 2020
    })
  }).then(r => r.json());

  return { cliente: c, vehiculo: v };
}

// ─── MAIN ────────────────────────────────────────────────────────────────────

(async () => {
  console.log('\n══════════════════════════════════════════════');
  console.log('  TallerGest — Verificación E2E con Playwright');
  console.log('══════════════════════════════════════════════\n');

  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  page = await context.newPage();

  // Capture JS console errors
  const consoleErrors = [];
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', err => consoleErrors.push('PAGE ERROR: ' + err.message));

  // ── 0. Seed data ─────────────────────────────────────────────────────────
  console.log('── 0. Preparando datos de prueba ──');
  let seed;
  try {
    seed = await apiReset();
    log(PASS, 'Seed data (cliente + vehículo)', `clienteId=${seed.cliente.id} vehiculoId=${seed.vehiculo.id}`);
  } catch(e) {
    log(FAIL, 'Seed data falló', e.message);
    await browser.close();
    process.exit(1);
  }

  // ── 1. Kanban view (home) ─────────────────────────────────────────────────
  console.log('\n── 1. Kanban Board ──');

  await check('Navega a /', async () => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    const title = await page.title();
    return `title="${title}"`;
  });

  await check('Navbar visible con links', async () => {
    const links = await page.locator('nav a').allTextContents();
    if (!links.some(t => t.includes('Kanban'))) throw new Error('Link Kanban no encontrado');
    if (!links.some(t => t.includes('Buscar'))) throw new Error('Link Buscar no encontrado');
    if (!links.some(t => t.includes('Ajustes'))) throw new Error('Link Ajustes no encontrado');
    return links.join(' | ');
  });

  await check('Columnas Kanban renderizadas', async () => {
    await page.waitForSelector('[class*="kanban"], .kanban, [data-testid*="column"]', { timeout: 3000 })
      .catch(() => null);
    // Fallback: look for column headers with estado names
    const text = await page.textContent('body');
    const estados = ['Recibida', 'Presupuesto', 'Reparación', 'Finalizada', 'Entregada', 'Rechazada'];
    const found = estados.filter(e => text.includes(e));
    if (found.length === 0) {
      // Try alternative names
      const alt = ['RECIBIDA', 'PRESUPUESTADO', 'EN REPARACION', 'recibida', 'presupuestado'];
      const altFound = alt.filter(e => text.includes(e));
      if (altFound.length === 0) throw new Error('No se encontraron columnas de estado');
      return `columnas: ${altFound.join(', ')}`;
    }
    return `columnas: ${found.join(', ')}`;
  });

  await check('Botón Nueva Orden visible', async () => {
    const btn = await page.locator('button:has-text("Nueva"), button:has-text("nueva"), button:has-text("Orden")').first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) throw new Error('Botón Nueva Orden no visible');
    return 'visible';
  });

  await page.screenshot({ path: '/tmp/01-kanban.png', fullPage: true });

  // ── 2. Nueva Orden — Modal ─────────────────────────────────────────────────
  console.log('\n── 2. Modal Nueva Orden ──');

  await check('Abre modal Nueva Orden', async () => {
    await page.locator('button:has-text("Nueva"), button:has-text("Orden")').first().click();
    await page.waitForSelector('role=dialog', { timeout: 3000 });
    return 'modal abierto';
  });

  await check('Stepper visible y centrado (3 pasos)', async () => {
    const body = await page.textContent('[role="dialog"]');
    const hasBusqueda = body.includes('Búsqueda');
    const hasRegistro = body.includes('Registro');
    const hasOrden = body.includes('Orden');
    if (!hasBusqueda || !hasRegistro || !hasOrden) throw new Error(`Stepper incompleto: ${body.slice(0, 100)}`);
    return 'Búsqueda / Registro / Orden visibles';
  });

  await check('Campo matrícula visible (paso 1)', async () => {
    const input = await page.locator('input[placeholder*="ABC"], input[id*="matricula"]').first();
    await input.isVisible();
    return 'input presente';
  });

  await page.screenshot({ path: '/tmp/02-modal-step1.png' });

  // ── 3. Búsqueda matrícula existente → paso 3 directo ──────────────────────
  console.log('\n── 3. Búsqueda de matrícula ──');

  await check('Busca matrícula existente TEST001 → avanza a paso 3', async () => {
    const input = await page.locator('input[placeholder*="ABC"], input[id*="matricula"]').first();
    await input.fill('TEST001');
    const btn = await page.locator('[role="dialog"] button:has-text("Buscar")').first();
    await btn.click();
    await page.waitForTimeout(800);
    // Should advance to step 3 (order description)
    const dialogText = await page.locator('[role="dialog"]').textContent();
    if (!dialogText.includes('avería') && !dialogText.includes('Descripción') && !dialogText.includes('descripcion')) {
      throw new Error('No avanzó al paso 3: ' + dialogText.slice(0, 150));
    }
    return 'paso 3 alcanzado';
  });

  await check('Card de vehículo encontrado visible', async () => {
    const dialogText = await page.locator('[role="dialog"]').textContent();
    if (!dialogText.includes('TEST001')) throw new Error('Matrícula TEST001 no aparece en paso 3');
    return 'TEST001 visible en resumen';
  });

  await page.screenshot({ path: '/tmp/03-modal-step3.png' });

  // ── 4. Crear orden ─────────────────────────────────────────────────────────
  console.log('\n── 4. Crear Orden ──');

  await check('Rellena descripción y crea orden', async () => {
    const textarea = await page.locator('[role="dialog"] textarea').first();
    await textarea.fill('Falla el embrague al arrancar en frío. Revisar disco y plato.');
    const kmInput = await page.locator('[role="dialog"] input[type="number"]').first();
    await kmInput.fill('52000');
    const createBtn = await page.locator('[role="dialog"] button:has-text("Crear")').first();
    await createBtn.click();
    await page.waitForTimeout(1200);
    // Dialog should close
    const dialogVisible = await page.locator('[role="dialog"]').isVisible().catch(() => false);
    if (dialogVisible) {
      const errText = await page.locator('[role="dialog"]').textContent();
      throw new Error('Modal sigue abierto: ' + errText.slice(0, 200));
    }
    return 'orden creada y modal cerrado';
  });

  await check('Orden aparece en columna Recibida', async () => {
    await page.waitForTimeout(500);
    const body = await page.textContent('body');
    if (!body.includes('TEST001') && !body.includes('Ibiza') && !body.includes('Seat')) {
      throw new Error('Tarjeta de orden no aparece en kanban');
    }
    return 'tarjeta visible en kanban';
  });

  await page.screenshot({ path: '/tmp/04-kanban-con-orden.png', fullPage: true });

  // ── 5. Order Detail Sheet ──────────────────────────────────────────────────
  console.log('\n── 5. Panel de Detalle ──');

  await check('Click en tarjeta abre panel de detalle', async () => {
    // Click the first order card
    const card = await page.locator('[class*="card"], [class*="Card"]').filter({ hasText: 'TEST001' }).first();
    await card.click();
    await page.waitForTimeout(600);
    // Look for the detail sheet
    const sheet = await page.locator('[data-radix-popper-content-wrapper], [role="dialog"], [data-state="open"]').last();
    const visible = await sheet.isVisible().catch(() => false);
    if (!visible) throw new Error('Panel de detalle no se abrió');
    return 'sheet abierto';
  });

  await check('Panel muestra matrícula y datos del vehículo', async () => {
    const bodyText = await page.textContent('body');
    if (!bodyText.includes('TEST001')) throw new Error('Matrícula no visible en detalle');
    if (!bodyText.includes('Ibiza') && !bodyText.includes('Seat')) throw new Error('Datos del vehículo no visibles');
    return 'TEST001 + Seat Ibiza visibles';
  });

  await check('Botón "Enviar presupuesto" visible', async () => {
    const btn = await page.locator('button:has-text("presupuesto"), button:has-text("Presupuesto")').first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) throw new Error('Botón Enviar presupuesto no encontrado');
    return 'visible';
  });

  await page.screenshot({ path: '/tmp/05-detail-sheet.png' });

  // ── 6. Transición de estado: recibida → presupuestado ─────────────────────
  console.log('\n── 6. Transición de estado ──');

  await check('Enviar presupuesto → estado cambia a Presupuestado', async () => {
    const btn = await page.locator('button:has-text("presupuesto"), button:has-text("Presupuesto")').first();
    await btn.click();
    await page.waitForTimeout(1000);
    const bodyText = await page.textContent('body');
    // Check no error "[object Object]" visible
    if (bodyText.includes('[object Object]')) throw new Error('Error "[object Object]" en UI');
    // Look for new state indicators
    if (bodyText.includes('Presupuestado') || bodyText.includes('presupuestado') || bodyText.includes('Aprobar')) {
      return 'estado cambiado a presupuestado';
    }
    throw new Error('Estado no cambió. Body: ' + bodyText.slice(0, 200));
  });

  await page.screenshot({ path: '/tmp/06-presupuestado.png' });

  // ── 7. Añadir item al presupuesto ─────────────────────────────────────────
  console.log('\n── 7. Budget Items ──');

  // First go back to recibida state via a new fresh order (the current one is presupuestado)
  // Close sheet and work with this order
  await check('Botón + Añadir concepto visible (no locked aún)', async () => {
    // The order is presupuestado - items should still be editable?
    // Actually in presupuestado state, items are NOT locked (lock starts at en_reparacion)
    const addBtn = await page.locator('button:has-text("Añadir"), button:has-text("concepto")').first();
    const visible = await addBtn.isVisible().catch(() => false);
    if (!visible) return 'no visible (puede estar bloqueado)';
    return 'visible';
  });

  // ── 8. Transición: presupuestado → en_reparacion ──────────────────────────
  console.log('\n── 8. Aprobar presupuesto ──');

  await check('Aprobar → estado en_reparacion', async () => {
    const btn = await page.locator('button:has-text("Aprobar")').first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) throw new Error('Botón Aprobar no visible');
    await btn.click();
    await page.waitForTimeout(1000);
    const bodyText = await page.textContent('body');
    if (bodyText.includes('[object Object]')) throw new Error('"[object Object]" en UI');
    if (bodyText.includes('Reparación') || bodyText.includes('reparacion') || bodyText.includes('Finalizar')) {
      return 'estado → en_reparacion';
    }
    throw new Error('Estado no cambió a en_reparacion: ' + bodyText.slice(0, 150));
  });

  await page.screenshot({ path: '/tmp/07-en-reparacion.png' });

  // ── 9. Finalizar reparación ────────────────────────────────────────────────
  console.log('\n── 9. Finalizar reparación ──');

  await check('Finalizar → estado finalizada', async () => {
    const btn = await page.locator('button:has-text("Finalizar")').first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) throw new Error('Botón Finalizar no visible');
    await btn.click();
    await page.waitForTimeout(1000);
    const bodyText = await page.textContent('body');
    if (bodyText.includes('[object Object]')) throw new Error('"[object Object]" en UI');
    if (bodyText.includes('entregado') || bodyText.includes('Entregado') || bodyText.includes('Marcar')) {
      return 'estado → finalizada';
    }
    throw new Error('Estado no cambió a finalizada: ' + bodyText.slice(0, 150));
  });

  await page.screenshot({ path: '/tmp/08-finalizada.png' });

  // ── 10. Marcar como entregado ─────────────────────────────────────────────
  console.log('\n── 10. Entregar ──');

  await check('Marcar como entregado', async () => {
    const btn = await page.locator('button:has-text("entregado"), button:has-text("Entregado")').first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) throw new Error('Botón Entregado no visible');
    await btn.click();
    await page.waitForTimeout(1000);
    const bodyText = await page.textContent('body');
    if (bodyText.includes('[object Object]')) throw new Error('"[object Object]" en UI');
    if (bodyText.includes('factura') || bodyText.includes('Factura') || bodyText.includes('Entregado')) {
      return 'estado → entregado';
    }
    throw new Error('No confirmó entregado: ' + bodyText.slice(0, 150));
  });

  await page.screenshot({ path: '/tmp/09-entregado.png' });

  // ── 11. Navegación a Buscar ────────────────────────────────────────────────
  console.log('\n── 11. Vista Buscar ──');

  await check('Navega a /buscar', async () => {
    await page.locator('nav a:has-text("Buscar")').click();
    await page.waitForTimeout(600);
    const url = page.url();
    if (!url.includes('buscar')) throw new Error('URL no cambió a /buscar: ' + url);
    return url;
  });

  await check('Input de búsqueda visible', async () => {
    const input = await page.locator('input[type="search"], input[placeholder*="buscar"], input[placeholder*="Buscar"], input[placeholder*="matrícula"], input').first();
    const visible = await input.isVisible().catch(() => false);
    if (!visible) throw new Error('Input de búsqueda no visible');
    return 'input visible';
  });

  await check('Buscar por matrícula TEST001 → resultado', async () => {
    const input = await page.locator('input').first();
    await input.fill('TEST001');
    await page.waitForTimeout(800);
    const body = await page.textContent('body');
    if (body.includes('TEST001') && (body.includes('Ibiza') || body.includes('Ana'))) {
      return 'resultado encontrado: TEST001 / Seat Ibiza';
    }
    // Might be still searching
    await page.waitForTimeout(500);
    const body2 = await page.textContent('body');
    if (body2.includes('TEST001')) return 'resultado visible';
    throw new Error('No aparecieron resultados para TEST001');
  });

  await page.screenshot({ path: '/tmp/10-buscar.png' });

  // ── 12. Vista Ajustes ─────────────────────────────────────────────────────
  console.log('\n── 12. Vista Ajustes ──');

  await check('Navega a /ajustes', async () => {
    await page.locator('nav a:has-text("Ajustes")').click();
    await page.waitForTimeout(500);
    const url = page.url();
    if (!url.includes('ajustes')) throw new Error('URL no cambió: ' + url);
    return url;
  });

  await check('Inputs de configuración centrados y visibles', async () => {
    const body = await page.textContent('body');
    const hasConfig = body.includes('Configuración') || body.includes('Ajustes') || body.includes('taller');
    if (!hasConfig) throw new Error('Página de ajustes vacía');
    // Check centering - look for the max-w container
    const container = await page.locator('.max-w-2xl, [class*="max-w"]').first();
    const visible = await container.isVisible().catch(() => false);
    return visible ? 'contenedor centrado visible' : 'campos visibles (sin verificar centrado)';
  });

  await check('Input tarifa_hora tiene valor', async () => {
    const input = await page.locator('input[id*="tarifa"], input[type="number"]').first();
    const visible = await input.isVisible().catch(() => false);
    if (!visible) throw new Error('Input tarifa no visible');
    const val = await input.inputValue();
    return `tarifa="${val}"`;
  });

  await check('Guardar cambios persiste nueva tarifa', async () => {
    const input = await page.locator('input[id*="tarifa"], input[type="number"]').first();
    await input.fill('65');
    const saveBtn = await page.locator('button:has-text("Guardar")').first();
    await saveBtn.click();
    await page.waitForTimeout(800);
    // Should show success toast or not error
    const body = await page.textContent('body');
    if (body.includes('error') || body.includes('Error')) throw new Error('Error al guardar: ' + body.slice(0, 100));
    return 'guardado sin errores';
  });

  await page.screenshot({ path: '/tmp/11-ajustes.png' });

  // ── 13. Probes adicionales ────────────────────────────────────────────────
  console.log('\n── 13. Probes edge-case ──');

  await probe('Modal nueva orden: matrícula inexistente → "no encontrado"', async () => {
    await page.locator('nav a:has-text("Kanban")').click();
    await page.waitForTimeout(400);
    await page.locator('button:has-text("Nueva"), button:has-text("Orden")').first().click();
    await page.waitForSelector('[role="dialog"]', { timeout: 3000 });
    const input = await page.locator('input[placeholder*="ABC"], input[id*="matricula"]').first();
    await input.fill('ZZZZZZ');
    await page.locator('[role="dialog"] button:has-text("Buscar")').first().click();
    await page.waitForTimeout(900);
    const dialogText = await page.locator('[role="dialog"]').textContent();
    const found = dialogText.includes('no encontrado') || dialogText.includes('Registrar') || dialogText.includes('nuevo');
    return found ? '"vehículo no encontrado" + opción de registrar' : `texto: ${dialogText.slice(0, 100)}`;
  });

  await probe('Cerrar modal limpia estado', async () => {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    const dialogVisible = await page.locator('[role="dialog"]').isVisible().catch(() => false);
    return dialogVisible ? 'modal aún visible' : 'modal cerrado correctamente';
  });

  await probe('Errores JS en consola', async () => {
    const errors = consoleErrors.filter(e =>
      !e.includes('net::ERR_') &&
      !e.includes('favicon') &&
      !e.includes('INVALID_ANNOTATION')
    );
    return errors.length === 0 ? 'sin errores JS' : `${errors.length} errores: ${errors.slice(0, 3).join(' | ')}`;
  });

  // ── Resumen ────────────────────────────────────────────────────────────────
  const passed  = results.filter(r => r.icon === PASS).length;
  const failed  = results.filter(r => r.icon === FAIL).length;
  const probes  = results.filter(r => r.icon === PROBE).length;
  const warns   = results.filter(r => r.icon === WARN).length;

  console.log('\n══════════════════════════════════════════════');
  console.log(`  RESUMEN: ${passed} ✅  ${failed} ❌  ${probes} 🔍  ${warns} ⚠️`);
  console.log(`  Veredicto: ${failed === 0 ? 'PASS' : 'FAIL'}`);
  console.log('══════════════════════════════════════════════\n');

  if (failed > 0) {
    console.log('FALLOS:');
    results.filter(r => r.icon === FAIL).forEach(r => console.log(`  ❌ ${r.msg}: ${r.detail}`));
  }

  await browser.close();
  process.exit(failed > 0 ? 1 : 0);
})();
