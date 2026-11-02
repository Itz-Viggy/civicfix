import {afterEach,expect,it,vi} from 'vitest'
import {cleanup,render,screen,waitFor} from '@testing-library/react'
import App from './App'
vi.mock('./MapPicker',()=>({default:()=> <div>Map coordinate alternative</div>}))
afterEach(()=>{cleanup();localStorage.clear();vi.unstubAllGlobals()})
it('recovers an expired draft and explains privacy and the manual reporting boundary',async()=>{
 localStorage.setItem('civicfix-draft','expired')
 vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{const url=String(input);if(url.endsWith('/session'))return new Response(JSON.stringify({csrf_token:'test'}));if(url.endsWith('/capabilities'))return new Response(JSON.stringify({simulated:true}));if(url.endsWith('/drafts/expired'))return new Response(JSON.stringify({error:{code:'not_found',message:'Unavailable'}}),{status:404});return new Response(JSON.stringify({draft:{id:'new',revision:1,state:'draft',expires_at:'2099-01-01T12:00:00Z',description:'',user_observations:'',eligibility:{can_analyze:false,can_review:false,can_prepare:false}}}))}))
 render(<App/>);await screen.findByRole('heading',{name:'Start with a photo'});expect(screen.getByText(/Simulated test mode/)).toBeInTheDocument();expect(screen.getByText(/you submit it yourself/)).toBeInTheDocument();expect(screen.getByLabelText('Upload issue photo')).toBeInTheDocument();await waitFor(()=>expect(localStorage.getItem('civicfix-draft')).toBe('new'))
})
it('shows typed AI failure and preserves an explicit manual correction path',async()=>{
 localStorage.setItem('civicfix-draft','failed')
 const draft={id:'failed',revision:5,state:'needs_correction',expires_at:'2099-01-01T12:00:00Z',description:'',user_observations:'',category:'pothole',photo:{id:'p'},analysis:{job_id:'j',status:'failed',classifier:{status:'ok',result:{predicted_category:'pothole'}},description:{status:'error',error:{code:'invalid_output',message:'Model response failed validation.'}},reason_codes:['description_failed']},eligibility:{can_analyze:true,can_review:false,can_prepare:false}}
 vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{const url=String(input);return new Response(JSON.stringify(url.endsWith('/session')?{csrf_token:'test'}:url.endsWith('/capabilities')?{simulated:false}:{draft}))}))
 render(<App/>);await screen.findByRole('heading',{name:'A useful starting point'});expect(screen.getByText('Model response failed validation.')).toBeInTheDocument();expect(screen.getByText(/Needs correction: Description failed/)).toBeInTheDocument();expect(screen.getByRole('button',{name:'Confirm my category and description'})).toBeDisabled();expect(screen.getByLabelText('Reason for manual confirmation')).toBeInTheDocument()
})
