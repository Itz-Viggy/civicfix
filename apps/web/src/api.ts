import type {components} from './generated-api'
export type Location = components['schemas']['LocationInput'] & {confirmed?:boolean;boundary_status?:string}
export type Stage = components['schemas']['ClassifierExecution'] | components['schemas']['DescriptionExecution']
export type Draft = components['schemas']['DraftView']
export type Capabilities = {simulated?:boolean;disclosure_version?:string;categories?:string[];[key:string]:unknown}
export type Preparation = {report_text:string;portal_url?:string;destination?:{portal_url?:string};route?:{portal_url?:string};message?:string;[key:string]:unknown}
export class ApiError extends Error {constructor(public status:number,public code:string,message:string,public reasons:string[]=[]){super(message)}}
let csrf=''
export async function request<T=any>(path:string, options:RequestInit={}, revision?:number):Promise<T>{
 const headers=new Headers(options.headers)
 if(options.method && options.method!=='GET'){if(csrf)headers.set('X-CSRF-Token',csrf);if(!(options.body instanceof FormData))headers.set('Content-Type','application/json');if(revision!==undefined)headers.set('If-Match',`"${revision}"`)}
 const response=await fetch(`/api/v1${path}`,{credentials:'same-origin',cache:'no-store',...options,headers})
 if(!response.ok){let data:any={};try{data=await response.json()}catch{};throw new ApiError(response.status,data.error?.code||'network_error',data.error?.message||`Request failed (${response.status}).`,data.error?.reason_codes||[])}
 if(response.status===204)return undefined as T
 return response.json()
}
export async function session(){const result=await request<{csrf_token:string}>('/session',{method:'POST',body:'{}'});csrf=result.csrf_token}
export const photoURL=(d:Draft)=>`/api/v1/drafts/${d.id}/photo?v=${d.photo?.id||''}`
export const labels:Record<string,string>={pothole:'Pothole',broken_streetlight:'Broken streetlight',damaged_sign:'Damaged sign',leaking_hydrant:'Leaking hydrant',illegal_dumping:'Suspected dumping'}
export function humanize(value:string){return value.replaceAll('_',' ').replace(/^./,x=>x.toUpperCase())}
