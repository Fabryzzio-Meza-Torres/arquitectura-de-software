import { expect, request as playwrightRequest, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

async function sessionToken(api, userId) {
  const response = await api.post('/api/demo/session', { data: { user_id: userId } })
  expect(response.ok()).toBeTruthy()
  return (await response.json()).access_token
}

function bearer(token) {
  return { Authorization: `Bearer ${token}` }
}

test('Phase 1 API happy path appears in client UI and Swagger is interactive', async ({ page }) => {
  const api = await playwrightRequest.newContext({ baseURL: 'http://127.0.0.1:8000' })
  const clientToken = await sessionToken(api, 1)
  const brokerToken = await sessionToken(api, 3)
  const leasingToken = await sessionToken(api, 2)
  const ruc = `20${Date.now().toString().slice(-9)}`
  const machineryName = `Excavadora E2E ${ruc.slice(-4)}`

  let response = await api.post('/api/requests', {
    headers: bearer(clientToken),
    data: {
      ruc, machinery_type: machineryName, requested_term_months: 12,
      requested_amount: 250000, currency: 'PEN', expected_settlement_date: '2027-12-20',
    },
  })
  expect(response.ok()).toBeTruthy()
  const application = await response.json()
  for (const kind of ['BANK_STATEMENTS', 'TAX_RETURN', 'PROJECT_CONTRACT']) {
    response = await api.post(`/api/requests/${application.id}/documents`, {
      headers: bearer(clientToken),
      multipart: {
        kind,
        file: { name: `${kind}.pdf`, mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 E2E') },
      },
    })
    expect(response.ok()).toBeTruthy()
  }
  response = await api.post(`/api/requests/${application.id}/submit`, {
    headers: bearer(clientToken), data: { bureau_scenario: 'SUCCESS', bureau_score: 720 },
  })
  expect(response.ok()).toBeTruthy()

  response = await api.post(`/api/requests/${application.id}/negotiation`, { headers: bearer(brokerToken) })
  const negotiation = await response.json()
  response = await api.post(`/api/negotiations/${negotiation.id}/documents`, {
    headers: bearer(brokerToken),
    multipart: {
      summary: 'Contrato E2E completo y compartido', structured_details: '{"source":"e2e"}',
      file: { name: 'contract.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 contract') },
    },
  })
  expect(response.ok()).toBeTruthy()

  response = await api.post('/api/integrations/risk-outcomes', {
    headers: { 'X-Integration-Key': 'poc-risk-secret' },
    data: {
      application_id: application.id, outcome: 'APPROVED', reason_code: 'E2E_EXTERNAL_APPROVED',
      reason_text: 'External evaluator approved the E2E application.', approved_limit: 250000,
      approved_term_months: 12, annual_interest_rate: 12,
    },
  })
  expect(response.ok()).toBeTruthy()
  response = await api.post(`/api/requests/${application.id}/simulations`, {
    headers: bearer(clientToken), data: { grace_months: 0, frequency: 'MONTHLY', balloon_percent: 0 },
  })
  const simulation = await response.json()
  await api.post(`/api/simulations/${simulation.id}/accept`, {
    headers: bearer(clientToken), data: { signer_confirmation: 'César — Head of Finance' },
  })
  response = await api.post(`/api/requests/${application.id}/activate`, {
    headers: bearer(leasingToken), data: { exchange_rate: 1 },
  })
  expect(response.ok()).toBeTruthy()

  await page.goto('/')
  await page.getByRole('button', { name: /César/ }).click()
  await expect(page.getByText('Capital listo para el proyecto.')).toBeVisible()
  await expect(page.getByText(machineryName)).toBeVisible()
  await expect(page.getByText(/Contrato activo/)).toBeVisible()

  await page.setViewportSize({ width: 360, height: 800 })
  const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
  expect(accessibility.violations).toEqual([])

  await page.goto('http://127.0.0.1:8000/docs')
  await expect(page.locator('.swagger-ui')).toBeVisible()
  await expect(page.locator('.info .title')).toContainText('Lea$e POC API')
  await api.dispose()
})
