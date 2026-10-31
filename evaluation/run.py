"""Real application adapter regression. Outputs remain private; never auto-label factuality."""
import asyncio,csv,hashlib,json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'services/api')]
from services.inference.manager import InferenceManager
from civicfix.images import sanitize
async def main():
    out=ROOT/'.runtime/app-evaluation'/time.strftime('%Y%m%d-%H%M%S');out.mkdir(parents=True)
    m=InferenceManager();await m.start()
    while any(s=='starting' for s in m.states.values()):await asyncio.sleep(.25)
    print(m.capabilities(),flush=True)
    selected=set(json.loads((ROOT/'experiments/description_evaluation/selection.json').read_text())['image_ids'])
    records=[]
    try:
        for row in csv.DictReader((ROOT/'data/labels.csv').open()):
            image_id=row['image_id'];p=ROOT/'data'/row['filename'];pixels,_=sanitize(p.read_bytes(),'image/jpeg')
            if image_id in selected:r=await m.analyze(pixels)
            else:
                # Exercise identical classifier adapter; omit expensive description on nonselected cases.
                state=m.states['description'];m.states['description']='unavailable'
                try:r=await m.analyze(pixels)
                finally:m.states['description']=state
            record={'image_id':image_id,'image_sha256':hashlib.sha256(pixels).hexdigest(),'expected':row['issue_type'],'description_selected':image_id in selected,**r}
            records.append(record)
            with (out/'results.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
            print(image_id,r['classifier']['status'],r['description']['status'] if image_id in selected else 'not-selected',flush=True)
        good=[r for r in records if r['classifier']['status']=='ok'];des=[r for r in records if r['description_selected']]
        summary={'attempted':len(records),'classification_valid':len(good),'classification_correct':sum(r['classifier']['result']['predicted_category']==r['expected'] for r in good),'description_attempted':len(des),'description_valid':sum(r['description']['status']=='ok' for r in des),'factuality':'Not yet reviewed; no factuality pass claimed','config':'app-description-v1 / clip-v2 / rgb-jpeg-1280-v1','records':str(out/'results.jsonl')}
        (out/'summary.json').write_text(json.dumps(summary,indent=2));print(summary,flush=True)
    finally:await m.close()
if __name__=='__main__':asyncio.run(main())
