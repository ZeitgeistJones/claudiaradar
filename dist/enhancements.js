// Data included with the repository and optionally refreshed by GitHub Actions.
// Newly discovered items are always marked Needs review until individually checked.
const researchBanner=document.createElement('p');
researchBanner.id='update-status';
researchBanner.className='micro';
researchBanner.style.cssText='padding:12px 0;color:#a8bea8;line-height:1.7';
document.querySelector('.stats')?.before(researchBanner);

const oldRender=render;
render=function(){
  oldRender();
  for(const button of document.querySelectorAll('[data-del]')){
    const found=rows.find(x=>x.id===button.dataset.del);
    if(!found||found.verification!=='Needs review')continue;
    const verify=document.createElement('button');
    verify.type='button'; verify.className='outline';verify.textContent='Review ✓';
    verify.style.marginRight='8px';
    verify.onclick=()=>{
      if(!confirm('Have you opened the original source, verified it is THIS Claudia, and checked that it is not a duplicate or paid/owned promotion?'))return;
      const tier=prompt('Audience tier: Niche / Crossover / Mainstream / Major','Niche');
      if(!['Niche','Crossover','Mainstream','Major'].includes(tier))return alert('Choose one of the four audience tiers.');
      const origin=prompt('Origin: Independent / Fan / community / Owned / official','Independent');
      if(!['Independent','Fan / community','Owned / official'].includes(origin))return alert('Choose a listed origin.');
      found.tier=tier;found.origin=origin;found.verification='Verified';
      found.notes=(found.notes||'')+' Manually reviewed '+new Date().toISOString().slice(0,10)+'.';
      save();render();
    };
    button.before(verify);
  }
};
(async function loadDiscovery(){
  try {
    const response=await fetch('./data/mentions.json',{cache:'no-store'});
    if(!response.ok)throw new Error('No data file');
    const data=await response.json();
    const incoming=[...(data.verified||[]),...(data.candidates||[])];
    const current=new Set(rows.map(x=>x.url));
    const valid=x=>x&&typeof x.title==='string'&&typeof x.url==='string'&&/^https?:\/\//i.test(x.url)&&/^\d{4}-\d{2}-\d{2}$/.test(x.date);
    for(const entry of incoming){
      if(!valid(entry)||current.has(entry.url))continue;
      rows.push({...entry,id:entry.id||'feed-'+rows.length});
      current.add(entry.url);
    }
    render();
    const stamp=document.getElementById('update-status');
    if(stamp)stamp.textContent='Source data last refreshed: '+(data.updatedAt?new Date(data.updatedAt).toLocaleString():'unknown')+' · New discoveries require review';
  } catch(err){
    const stamp=document.getElementById('update-status');
    if(stamp)stamp.textContent='Research feed unavailable · Manual entries still work';
  }
})();
