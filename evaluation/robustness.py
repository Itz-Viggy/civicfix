"""Small explicitly synthetic/reused robustness suite; never held-out accuracy."""
import asyncio,io,json,sys,time,hashlib,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'services/api')]
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
from civicfix.images import sanitize
from services.inference.manager import InferenceManager
async def main():
    out=ROOT/'.runtime/app-evaluation'/('robustness-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(parents=True)
    cases=[]
    for i in range(2):
        road=Image.new('RGB',(640,480),(85+i*15,85+i*15,85+i*15));ImageDraw.Draw(road).line([(320,0),(320,480)],fill='white',width=8)
        cases.append((f'normal-synthetic-{i}',road,'Programmatically drawn intact road; artificial sanity check, CC0 author-generated'))
        unrelated=Image.new('RGB',(640,480),'skyblue');ImageDraw.Draw(unrelated).ellipse((100+i*60,80,400,380),fill='orange')
        cases.append((f'unrelated-synthetic-{i}',unrelated,'Programmatically drawn abstract shapes; CC0 author-generated'))
    rows=list(csv.DictReader((ROOT/'data/labels.csv').open()))
    a=Image.open(ROOT/'data'/rows[0]['filename']).convert('RGB');b=Image.open(ROOT/'data'/rows[-1]['filename']).convert('RGB')
    cases.extend([('blur-reused',a.filter(ImageFilter.GaussianBlur(25)),rows[0]),('dark-reused',ImageEnhance.Brightness(a).enhance(.08),rows[0])])
    for i in range(2):
        multi=Image.new('RGB',(640,480));multi.paste(a.resize((320,480)),(0,0));multi.paste(b.resize((320,480)),(320,0));cases.append((f'multiple-composite-{i}',multi.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if i else multi,[rows[0],rows[-1]]))
    manifest=[{'id':id,'provenance':source,'independent_held_out':False} for id,_,source in cases];(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    m=InferenceManager();await m.start()
    while 'starting' in m.states.values():await asyncio.sleep(.25)
    try:
        for id,image,_ in cases:
            buf=io.BytesIO();image.save(buf,'JPEG');data,_=sanitize(buf.getvalue(),'image/jpeg')
            result=await m.analyze(data)
            with (out/'results.jsonl').open('a') as f:f.write(json.dumps({'id':id,**result})+'\n')
            print(id,result['description']['status'],flush=True)
    finally:await m.close()
if __name__=='__main__':asyncio.run(main())
