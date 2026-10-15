"""Turn per-product folders (介绍.txt plus >=2 pictures) into a reviewable batch plan."""
from pathlib import Path
import argparse,hashlib,json,re
def plan(folder,output):
    root=Path(folder).resolve();target=Path(output).resolve()
    if not root.is_dir() or target.parent!=root:raise ValueError('Save the new plan directly inside the product root folder')
    if target.exists():raise ValueError('Choose a new plan filename')
    jobs=[];errors=[]
    for sub in sorted(root.iterdir()):
        if not sub.is_dir() or sub.is_symlink():continue
        try:
            textfile=sub/'介绍.txt'
            if textfile.is_symlink() or not textfile.is_file():raise ValueError('Missing 介绍.txt')
            text=textfile.read_text(encoding='utf-8-sig').strip();sentences=[s.strip() for s in re.findall(r'[^。！？!?]+[。！？!?]?',text) if s.strip()]
            if not sentences or len(sentences)>30 or any(len(s)>160 for s in sentences):raise ValueError('Use 1..30 short sentences, each <=160 characters')
            images=sorted(p for p in sub.iterdir() if p.is_file() and not p.is_symlink() and p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'})
            if len(images)<2:raise ValueError('Provide at least two product pictures')
            rows=[]
            for i,s in enumerate(sentences):rows.append({'text':s,'images':[images[(2*i+j)%len(images)].relative_to(root).as_posix() for j in [0,1]]})
            job={'id':'product-'+hashlib.sha256(sub.name.encode()).hexdigest()[:12],'title':sub.name,'sentences':rows}
            from batch_product_videos import validate_job
            validate_job(job,root);jobs.append(job)
        except Exception as e:errors.append({'folder':sub.name,'error':str(e)})
    if not jobs:raise ValueError('No usable products: '+json.dumps(errors,ensure_ascii=False))
    if len(jobs)>50:raise ValueError('At most 50 products per batch; split the folder into smaller batches')
    data={'jobs':jobs,'planning':'Images assigned in filename order within each product, not semantic image matching. Review before rendering.','planning_errors':errors}
    with target.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
    return data
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder');p.add_argument('--out',required=True);a=p.parse_args();r=plan(a.folder,a.out);print('Products:',len(r['jobs']),'Planning errors:',len(r['planning_errors']));raise SystemExit(2 if r['planning_errors'] else 0)
