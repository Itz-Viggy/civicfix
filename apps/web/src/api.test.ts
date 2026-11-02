import {afterEach,describe,expect,it,vi} from 'vitest'
import {ApiError,humanize,request,session} from './api'
afterEach(()=>vi.unstubAllGlobals())
describe('private API boundary',()=>{
 it('sends the session CSRF token and quoted revision for a mutation',async()=>{
  const fetcher=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({csrf_token:'token'}))).mockResolvedValueOnce(new Response(JSON.stringify({draft:{revision:3}})))
  vi.stubGlobal('fetch',fetcher);await session();await request('/drafts/a',{method:'PATCH',body:JSON.stringify({description:'Reviewed condition'})},2)
  const headers=fetcher.mock.calls[1][1].headers as Headers
  expect(headers.get('X-CSRF-Token')).toBe('token');expect(headers.get('If-Match')).toBe('"2"');expect(fetcher.mock.calls[1][1].cache).toBe('no-store')
 })
 it('does not set a JSON content type on photo uploads',async()=>{const fetcher=vi.fn().mockResolvedValue(new Response('{}'));vi.stubGlobal('fetch',fetcher);await request('/drafts/a/photo',{method:'PUT',body:new FormData()},1);expect(fetcher.mock.calls[0][1].headers.get('Content-Type')).toBeNull()})
 it('preserves actionable server conflicts without pretending the write succeeded',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({error:{code:'revision_conflict',message:'Reload the current draft.',reason_codes:['stale_revision']}}),{status:409})));try{await request('/drafts/a',{method:'PATCH',body:'{}'},1);throw new Error('Expected rejection')}catch(e){expect(e).toBeInstanceOf(ApiError);expect((e as ApiError).code).toBe('revision_conflict');expect((e as ApiError).reasons).toEqual(['stale_revision'])}})
 it('accepts content-free deletion and formats reason codes',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(null,{status:204})));expect(await request('/drafts/a',{method:'DELETE'})).toBeUndefined();expect(humanize('unknown_ownership')).toBe('Unknown ownership')})
})
