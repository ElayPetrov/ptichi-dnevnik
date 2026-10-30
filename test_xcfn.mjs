// the helper's choosing and caching, run in Node with stand-ins for Supabase and xeno-canto
let fails=0;const check=(n,got,exp)=>{const ok=JSON.stringify(got)===JSON.stringify(exp);fails+=!ok;console.log((ok?'PASS ':'FAIL ')+n+(ok?'':'\n     got '+JSON.stringify(got)+'\n     exp '+JSON.stringify(exp)));};
const env={SUPABASE_URL:'https://sb.test',SUPABASE_SERVICE_ROLE_KEY:'srk',XC_KEY:'secret-key'};globalThis.Deno={env:{get:k=>env[k]}};
const {choose,handle}=await import('/tmp/xcfn.mjs');
const R=(id,cnt,type,q,len)=>({id:String(id),cnt,type,q,length:len,file:'https://xeno-canto.org/'+id+'/download',rec:'R'+id,lic:'//creativecommons.org/licenses/by-nc-sa/4.0/',url:'//xeno-canto.org/'+id});
const d=choose([R(1,'Germany','song','A','0:30'),R(2,'Bulgaria','song','B','0:40'),R(3,'Bulgaria','song','A','2:30'),R(4,'Greece','call','A','0:10'),R(5,'Bulgaria','call, song','A','0:20')]);
check('F1 Bulgaria first; a song of 40 s beats a better one of 2½ minutes', d.song.id,'2');
check('F2 a call that is only a call beats one mixed with song; neighbours before the rest', d.call.id,'4');
let calls=[],store={};
globalThis.fetch=async(u,o={})=>{calls.push(u);const url=new URL(u);
  if(url.host==='sb.test'){if((o.method||'GET')==='GET'){const sp=decodeURIComponent(url.search.split('sp=eq.')[1]);return new Response(JSON.stringify(store[sp]?[store[sp]]:[]),{status:200});}
    const b=JSON.parse(o.body);store[b.sp]={data:b.data,at:b.at};return new Response('',{status:201});}
  if(url.host==='xeno-canto.org'){const q=url.searchParams.get('query');
    if(url.searchParams.get('key')!=='secret-key')return new Response('',{status:401});
    if(q.includes('cnt:bulgaria'))return new Response(JSON.stringify({recordings:[R(10,'Bulgaria','song','A','0:25')]}));
    if(q.includes('area:europe'))return new Response(JSON.stringify({recordings:[R(11,'Romania','call','B','0:08')]}));
    return new Response(JSON.stringify({recordings:[]}));}
  return new Response('',{status:404});};
let r=await handle(new Request('https://fn.test/xc?sp=Turdus%20merula'));let j=await r.json();
check('F3 asks xeno-canto with the secret key: Bulgaria for the song, Europe for the missing call', [j.song.id,j.call.id,calls.filter(c=>c.includes('xeno-canto')).length],['10','11',2]);
check('F4 the answer carries no key', JSON.stringify(j).includes('secret-key'), false);
calls=[];r=await handle(new Request('https://fn.test/xc?sp=Turdus%20merula'));j=await r.json();
check('F5 the second time it comes from the shared memory, without asking xeno-canto', [j.song.id,calls.filter(c=>c.includes('xeno-canto')).length],['10',0]);
r=await handle(new Request('https://fn.test/xc?sp=drop%20table'));
check('F6 anything but a Latin name is refused', r.status, 400);
r=await handle(new Request('https://fn.test/xc',{method:'OPTIONS'}));
check('F7 the browser\'s pre-check is answered (CORS)', r.headers.get('Access-Control-Allow-Origin'),'*');
console.log('FAILURES:',fails);
