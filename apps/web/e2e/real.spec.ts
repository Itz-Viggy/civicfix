import {test,expect} from '@playwright/test'
import {fileURLToPath} from 'node:url'
test('real local models through browser to reviewed handoff',async({page,request})=>{
 test.skip(process.env.CIVICFIX_E2E_REAL!=='1','Explicit real-model smoke; normal E2E uses labeled fixtures')
 test.setTimeout(180000)
 await expect.poll(async()=>{const c=await(await request.get('http://127.0.0.1:8000/api/v1/capabilities')).json();return c.classifier.status==='ready'&&c.description.status==='ready'},{timeout:125000}).toBe(true)
 await page.route('https://tile.openstreetmap.org/**',r=>r.abort());await page.goto('/')
 await page.getByLabel('Upload issue photo').setInputFiles(fileURLToPath(new URL('../../../data/images/commons-0a68e3b438.jpg',import.meta.url)))
 await page.getByLabel('Latitude',{exact:true}).fill('29.645781879176276');await page.getByLabel('Longitude',{exact:true}).fill('-82.30619912751014');await page.getByLabel('Describe the location').fill('SE 7th Avenue test location');await page.getByRole('button',{name:'Confirm location'}).click()
 await page.getByLabel('I understand the models may be wrong').check();await page.getByRole('button',{name:'Analyze photo',exact:true}).click();await expect(page.getByRole('button',{name:'Analyze again'})).toBeEnabled({timeout:65000})
 await page.getByLabel('Issue category').selectOption('pothole');await page.getByLabel('Issue description').fill('A hole with broken pavement is visible beside a square metal cover.')
 await page.getByText('Resolve uncertainty or complete manually',{exact:true}).click();await page.getByLabel('Reason for manual confirmation').fill('Checked the photo and removed uncertain statements.');await page.getByRole('button',{name:'Confirm my category and description'}).click();await expect(page.getByText('Manual correction recorded.',{exact:false})).toBeVisible()
 await page.getByRole('button',{name:'Continue to review'}).click();await page.getByLabel('I reviewed the photo').check();await page.getByRole('button',{name:'Prepare Report',exact:true}).click();await expect(page.getByRole('heading',{name:'Report Prepared',exact:true})).toBeVisible()
 const link=page.getByRole('link',{name:'Open official reporting form'});await expect(link).toHaveAttribute('href','https://gainesvillefl.citysourced.com/servicerequests/create')
 await page.screenshot({path:'test-results/real-prepared.png',fullPage:true})
 await page.getByRole('button',{name:'Clear draft and photo'}).click()
})
