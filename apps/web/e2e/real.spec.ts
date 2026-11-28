import {test, expect, type Page} from '@playwright/test'
import {readFile} from 'node:fs/promises'
import {resolve} from 'node:path'
import {fileURLToPath} from 'node:url'
import type {components} from '../src/generated-api'

type Draft = components['schemas']['DraftView']

const root = fileURLToPath(new URL('../../../', import.meta.url))
const photos = process.env.CIVICFIX_E2E_PHOTOS_DIR
  || resolve(root, '.runtime/goal-photo-verification')
const potholePhoto = resolve(root, 'data/images/commons-0a68e3b438.jpg')
const location = {
  latitude: 29.645781879176276,
  longitude: -82.30619912751014,
  label: 'SE 7th Avenue test location',
}
const note = 'The square metal cover is just left of the hole.'
const destination = 'myGNV — City nonemergency intake'
const externalServer = Boolean(process.env.CIVICFIX_E2E_BASE_URL)
const analysisWait = externalServer ? 1050000 : 65000

test.skip(process.env.CIVICFIX_E2E_REAL !== '1', 'Requires the real local model workers')

test.beforeEach(async ({page, request}) => {
  test.setTimeout(externalServer ? 1800000 : 180000)
  const api = process.env.CIVICFIX_E2E_BASE_URL || 'http://127.0.0.1:8000'
  await expect.poll(async () => {
    const response = await request.get(api + '/api/v1/capabilities')
    if (!response.ok()) return false
    const caps = await response.json()
    return caps.simulated === false && caps.classifier.status === 'ready' && caps.description.status === 'ready'
  }, {timeout: externalServer ? 650000 : 125000}).toBe(true)

  await page.route('https://tile.openstreetmap.org/**', route => route.abort())
  await page.goto('/')
})

async function confirmLocation(page: Page, point: typeof location) {
  await page.getByLabel('Latitude', {exact: true}).fill(String(point.latitude))
  await page.getByLabel('Longitude', {exact: true}).fill(String(point.longitude))
  await page.getByLabel('Describe the location').fill(point.label)
  await page.getByRole('button', {name: 'Confirm location'}).click()
}

async function upload(page: Page, photo: string, point = location) {
  const input = page.getByLabel('Upload issue photo')
  await expect(input).toBeEnabled()
  const uploaded = page.waitForResponse(response => response.request().method() === 'PUT'
    && /\/api\/v1\/drafts\/[^/]+\/photo$/.test(new URL(response.url()).pathname))
  await input.setInputFiles(photo)
  expect((await uploaded).ok()).toBe(true)
  await confirmLocation(page, point)
  await page.getByLabel('I understand the models may be wrong').check()
}

async function currentDraft(page: Page): Promise<Draft> {
  const id = await page.evaluate(() => localStorage.getItem('civicfix-draft'))
  expect(id).toBeTruthy()
  const response = await page.request.get('/api/v1/drafts/' + id)
  expect(response.ok()).toBe(true)
  return (await response.json()).draft
}

test('clear pothole goes from real classification to the downloaded report', async ({page}, testInfo) => {
  await upload(page, potholePhoto)
  await page.getByLabel('Your observations').fill(note)
  await page.getByRole('button', {name: 'Analyze photo', exact: true}).click()
  await expect(page.getByRole('button', {name: 'Analyze again'})).toBeEnabled({timeout: analysisWait})
  await expect(page.getByLabel('Issue category')).toHaveValue('pothole')

  const {analysis} = await currentDraft(page)
  expect(analysis?.status).toBe('succeeded')
  expect(analysis?.reason_codes).toEqual([])
  expect(analysis?.classifier).toMatchObject({
    status: 'ok', metadata: {adapter: 'openclip_local', simulated: false},
    result: {predicted_category: 'pothole', outcome: 'supported'},
  })
  expect(analysis?.description).toMatchObject({
    status: 'ok', metadata: {simulated: false},
    result: {category_suggestion: 'pothole', outcome: 'supported'},
  })
  expect(analysis?.description?.metadata?.adapter).toMatch(/^qwen_/)
  const description = analysis?.description?.result?.suggested_description ?? ''
  expect(description).toMatch(/pothole|hole|cavity|depression/i)
  expect(description).toMatch(/asphalt|pavement/i)
  expect(description).toMatch(/cover/i)
  await expect(page.getByLabel('Issue description')).toHaveValue(description)
  await expect(page.getByLabel('Your observations')).toHaveValue(note)

  await page.getByRole('button', {name: 'Continue to review'}).click()
  await page.getByLabel('I reviewed the photo').check()
  const preparing = page.waitForResponse(response => response.request().method() === 'POST'
    && /\/api\/v1\/drafts\/[^/]+\/prepare$/.test(new URL(response.url()).pathname))
  await page.getByRole('button', {name: 'Prepare Report', exact: true}).click()
  const response = await preparing
  expect(response.ok()).toBe(true)
  const prepared = await response.json()
  expect(prepared).toMatchObject({
    category: 'pothole', description, user_observations: note,
    location: {...location, confirmed: true}, field_sources: {category: 'clip', description: 'qwen'},
    destination: {status: 'resolved', jurisdiction: 'City of Gainesville', destination_name: destination},
  })
  await expect(page.getByRole('heading', {name: 'Report Prepared', exact: true})).toBeVisible()
  const link = page.getByRole('link', {name: 'Open official reporting form'})
  await expect(link).toHaveAttribute('href', 'https://gainesvillefl.citysourced.com/servicerequests/create')

  const downloading = page.waitForEvent('download')
  await page.getByRole('link', {name: 'Download text', exact: true}).click()
  const download = await downloading
  const reportPath = testInfo.outputPath('civicfix-report.txt')
  await download.saveAs(reportPath)
  const report = await readFile(reportPath, 'utf8')
  expect(report).toBe(prepared.report_text)
  for (const line of [description, note, location.label, destination]) expect(report).toContain(line)
  await testInfo.attach('Downloaded report', {path: reportPath, contentType: 'text/plain'})

  const downloadingPdf = page.waitForEvent('download')
  await page.getByRole('link', {name: 'Download PDF', exact: true}).click()
  const pdf = await downloadingPdf
  expect(pdf.suggestedFilename()).toBe('civicfix-report.pdf')
  const pdfPath = testInfo.outputPath('civicfix-report.pdf')
  await pdf.saveAs(pdfPath)
  expect((await readFile(pdfPath)).subarray(0, 5).toString()).toBe('%PDF-')
  await testInfo.attach('PDF report', {path: pdfPath, contentType: 'application/pdf'})
  await page.screenshot({path: testInfo.outputPath('prepared.png'), fullPage: true})
})

test('downtown pin asks for the affected road and resolves after correction', async ({page}, testInfo) => {
  const original = {latitude: 29.651600, longitude: -82.324800, label: 'Downtown Gainesville'}
  await upload(page, potholePhoto, original)
  await page.getByRole('button', {name: 'Analyze photo', exact: true}).click()
  await expect(page.getByRole('button', {name: 'Analyze again'})).toBeEnabled({timeout: analysisWait})
  await page.getByRole('button', {name: 'Continue to review'}).click()
  await expect(page.getByText('29.651600, -82.324800 · Confirmed')).toBeVisible()
  await expect(page.getByText('Source: clip', {exact: true})).toBeVisible()
  await expect(page.getByRole('heading', {name: 'Pinpoint the affected location'})).toBeVisible()
  await expect(page.getByText('Nearest mapped road · S MAIN ST', {exact: true})).toBeVisible()
  await expect(page.getByText(/enter its street name and nearest cross street/)).toBeVisible()
  await expect(page.getByRole('button', {name: 'Prepare Report', exact: true})).toBeDisabled()
  const draft = await currentDraft(page)
  expect(draft).toMatchObject({
    location: {...original, confirmed: true}, category: 'pothole', field_sources: {category: 'clip'},
    analysis: {status: 'succeeded', classifier: {metadata: {adapter: 'openclip_local', simulated: false}}},
    route: {status: 'unresolved', reason_codes: ['road_location_required'], jurisdiction: null},
  })
  await page.screenshot({path: testInfo.outputPath('location-clarification.png'), fullPage: true})

  await page.getByRole('button', {name: 'Edit location', exact: true}).click()
  await confirmLocation(page, {latitude: 29.651971, longitude: -82.325009, label: 'Main and University'})
  await page.getByRole('button', {name: 'Continue to review'}).click()
  await expect(page.getByText(/different maintenance records/)).toBeVisible()
  await expect(page.getByText(/away from the intersection/)).toBeVisible()
  expect((await currentDraft(page)).route?.reason_codes).toEqual(['road_maintainer_conflict'])

  await page.getByRole('button', {name: 'Edit location', exact: true}).click()
  await confirmLocation(page, {latitude: 29.651600, longitude: -82.325009, label: 'South Main St south of University Ave'})
  await page.getByRole('button', {name: 'Continue to review'}).click()
  await expect(page.getByRole('heading', {name: destination})).toBeVisible()
  await expect(page.getByText('City of Gainesville', {exact: true})).toBeVisible()
  await expect(page.getByText('Matched road · S MAIN ST', {exact: true})).toBeVisible()
  await expect(page.getByRole('heading', {name: 'Report text'})).toBeVisible()
  expect(await currentDraft(page)).toMatchObject({
    route: {status: 'resolved', jurisdiction: 'City of Gainesville'},
    field_sources: {category: 'clip'}, analysis: {job_id: draft.analysis?.job_id},
  })
  await page.getByLabel('I reviewed the photo').check()
  await page.getByRole('button', {name: 'Prepare Report', exact: true}).click()
  await expect(page.getByRole('heading', {name: 'Report Prepared', exact: true})).toBeVisible()
  await page.screenshot({path: testInfo.outputPath('corrected-prepared.png'), fullPage: true})
})

for (const {file, outcome, title, explanation} of [
  {file: 'astronaut.png', outcome: 'unsupported', title: 'No supported civic issue found',
    explanation: 'Choose a photo showing a pothole'},
  {file: 'blurred-pavement.jpg', outcome: 'unclear', title: 'The issue is unclear',
    explanation: 'Upload a sharper, well-lit photo'},
]) {
  test(`${outcome} photo stops at real classification`, async ({page}, testInfo) => {
    const reportCalls: string[] = []
    page.on('request', request => {
      const path = new URL(request.url()).pathname
      if (/\/api\/v1\/drafts\/[^/]+\/(destination|review|prepare|manual-resolution|(?:prepared|draft)\.txt)$/.test(path)) {
        reportCalls.push(path)
      }
    })
    await upload(page, resolve(photos, file))
    await page.getByRole('button', {name: 'Analyze photo', exact: true}).click()
    await expect(page.getByRole('heading', {name: title})).toBeVisible({timeout: analysisWait})
    await expect(page.getByRole('status').filter({hasText: title})).toContainText(explanation)
    await expect(page.getByRole('button', {name: 'Review & prepare', exact: false})).toBeDisabled()
    await expect(page.getByLabel('Issue category')).toHaveCount(0)
    await expect(page.getByRole('button', {name: 'Continue to review'})).toHaveCount(0)

    const draft = await currentDraft(page)
    expect(draft).toMatchObject({
      category: null, description: '', prepared_revision: null,
      eligibility: {can_analyze: false, can_review: false, can_prepare: false},
      analysis: {
        status: 'rejected', reason_codes: [`classification_${outcome}`], description: null,
        classifier: {status: 'ok', metadata: {adapter: 'openclip_local', simulated: false},
          result: {outcome, predicted_category: null}},
      },
    })
    expect(reportCalls).toEqual([])
    await page.screenshot({path: testInfo.outputPath('rejected.png'), fullPage: true})
    await page.getByRole('button', {name: 'Replace photo'}).click()
    await expect(page.getByLabel('Upload issue photo')).toBeEnabled()
  })
}
