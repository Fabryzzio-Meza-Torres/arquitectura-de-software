import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

function pdfBuffer(label) {
  return Buffer.from(`%PDF-1.4 ${label}`)
}

async function switchTo(page, firstName) {
  const changeRole = page.getByRole('button', { name: 'Cambiar rol' })
  if (await changeRole.isVisible().catch(() => false)) await changeRole.click()
  await page.getByRole('button', { name: new RegExp(firstName) }).click()
}

test('Lea$e Phase 1 happy path runs end to end through the UI (VG1-VG4)', async ({ page }) => {
  const ruc = `20${Date.now().toString().slice(-9)}`
  const machineryName = `Excavadora UI ${ruc.slice(-4)}`

  // --- César: Flow 1 — request financing, complete dossier, submit for review ---
  await page.goto('/')
  await switchTo(page, 'César')
  await expect(page.getByText('Capital listo para el proyecto.')).toBeVisible()

  await page.getByLabel('RUC').fill(ruc)
  await page.getByLabel('Maquinaria').fill(machineryName)
  await page.locator('input[name="requested_amount"]').fill('250000')
  await page.getByLabel('Plazo (meses)').fill('12')
  await page.getByLabel('Moneda').selectOption('PEN')
  await page.getByLabel('Liquidación del proyecto').fill('2028-12-20')
  await page.getByRole('button', { name: 'Crear solicitud' }).click()
  await expect(page.getByText(machineryName)).toBeVisible()

  for (const kind of ['BANK_STATEMENTS', 'TAX_RETURN', 'PROJECT_CONTRACT']) {
    await page.getByLabel(`Subir ${kind}`).setInputFiles({ name: `${kind}.pdf`, mimeType: 'application/pdf', buffer: pdfBuffer(kind) })
    await expect(page.getByText(`${kind} procesado.`)).toBeVisible()
  }
  await page.getByRole('button', { name: 'Enviar a revisión externa' }).click()
  await expect(page.getByText('Expediente enviado.')).toBeVisible()

  // --- Maxim: Flow 1B — open negotiation, propose meeting, share the contract PDF (VG1) ---
  await switchTo(page, 'Maxim')
  await page.getByRole('button', { name: 'Abrir o consultar' }).click()
  await expect(page.getByText('Negociación documental abierta.')).toBeVisible()

  await page.getByLabel('Fecha y hora').fill('2028-01-15T15:00')
  await page.getByRole('button', { name: 'Registrar propuesta' }).click()
  await expect(page.getByText(/Fecha propuesta por Maxim/)).toBeVisible()

  await page.getByRole('button', { name: 'Registrar idea' }).click()
  await expect(page.getByText('Propuesta no vinculante registrada.')).toBeVisible()

  await page.getByRole('button', { name: 'Registrar mensaje' }).click()
  await expect(page.getByText('Mensaje preservado en negociación.')).toBeVisible()

  await page.locator('input[name="file"]').setInputFiles({ name: 'contract.pdf', mimeType: 'application/pdf', buffer: pdfBuffer('contract') })
  await page.getByRole('button', { name: 'Compartir documento' }).click()
  await expect(page.getByText('PDF compartido con ambas empresas.')).toBeVisible()

  // --- César: accept the meeting date and confirm the shared PDF is visible ---
  await switchTo(page, 'César')
  await page.getByRole('button', { name: 'Aceptar' }).click()
  await expect(page.getByText('Respuesta registrada; Lea$e no tomó ninguna decisión por ti.')).toBeVisible()
  await expect(page.getByText('contract.pdf', { exact: true })).toBeVisible()

  // --- Juan Pedro: Flow 2 — record the external credit outcome (APPROVED) ---
  await switchTo(page, 'Juan Pedro')
  await page.getByRole('button', { name: new RegExp(machineryName) }).click()
  await page.locator('select[name="outcome"]').selectOption('APPROVED')
  await page.locator('input[name="annual_rate"]').fill('12')
  await page.getByRole('button', { name: 'Simular callback externo' }).click()
  await expect(page.getByText('Callback externo registrado. Lea$e no calculó el resultado.')).toBeVisible()

  // --- César: Flow 3 — simulate and digitally sign the schedule ---
  await switchTo(page, 'César')
  await page.getByRole('button', { name: 'Simular' }).click()
  await expect(page.getByText('Simulación generada con precisión decimal.')).toBeVisible()
  await page.getByRole('button', { name: 'Elegir y firmar' }).click()
  await expect(page.getByText('Cronograma firmado; hash de integridad registrado.')).toBeVisible()

  // --- Juan Pedro: activate — contract is created PENDING, no schedule yet ---
  await switchTo(page, 'Juan Pedro')
  await page.getByRole('button', { name: new RegExp(machineryName) }).click()
  await page.getByRole('button', { name: 'Activar una vez' }).click()
  await expect(page.getByText('Contrato y cronograma activados exactamente una vez.')).toBeVisible()

  // --- César: confirm reception — VG2, schedule is generated only now ---
  await switchTo(page, 'César')
  await expect(page.getByText('Confirmar recepción')).toBeVisible()
  await page.getByRole('button', { name: 'Confirmar recepción' }).click()
  await expect(page.getByText('Recepción confirmada; cronograma generado.')).toBeVisible()
  await expect(page.locator('.schedule-table')).toBeVisible()

  // --- César: Flow 4 — pay off every installment, idempotent by bank reference ---
  // Exact amounts are read from the API (raw Decimal, not the locale-formatted table cell)
  // so the final balance lands at exactly zero for the purchase-option check below.
  const clientToken = await page.evaluate(() => sessionStorage.getItem('lease-demo-token'))
  const contractsResponse = await page.request.get('/api/contracts', { headers: { Authorization: `Bearer ${clientToken}` } })
  const [apiContract] = await contractsResponse.json()
  for (const [index, installment] of apiContract.installments.entries()) {
    await page.locator('input[name="bank_reference"]').fill(`E2E-REF-${index}`)
    await page.locator('input[name="amount"]').fill(String(installment.amount))
    await page.getByRole('button', { name: 'Registrar pago' }).click()
    await expect(page.getByText(`E2E-REF-${index}`)).toBeVisible()
  }
  await expect(page.getByRole('button', { name: 'Ejercer opción de compra' })).toBeEnabled()

  // --- César: Flow 6 — resolve end of contract via the purchase option ---
  await page.getByRole('button', { name: 'Ejercer opción de compra' }).click()
  await expect(page.getByText('Opción de compra elegida.')).toBeVisible()

  // --- Juan Pedro: VG3 pronosticated income + VG4 process the closing branch ---
  await switchTo(page, 'Juan Pedro')
  await expect(page.getByText('Ingreso pronosticado')).toBeVisible()
  await page.getByRole('button', { name: /Procesar PURCHASE/ }).click()
  await expect(page.getByText('Cierre de contrato procesado.')).toBeVisible()
  await expect(page.getByText('COMPLETED PURCHASED').first()).toBeVisible()

  // --- Maxim: RBAC — no portfolio, no schedules, no collections summary ---
  await switchTo(page, 'Maxim')
  await expect(page.getByText('Broker · Negotiation facilitator')).toBeVisible()

  await page.setViewportSize({ width: 360, height: 800 })
  const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
  expect(accessibility.violations).toEqual([])

  await page.goto('http://127.0.0.1:8000/docs')
  await expect(page.locator('.swagger-ui')).toBeVisible()
  await expect(page.locator('.info .title')).toContainText('Lea$e POC API')
})
