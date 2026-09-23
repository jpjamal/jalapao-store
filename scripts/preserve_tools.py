"""Rebuild preserved utilities; original site remains intact for rollback."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent.parent
target = root / 'frontend/public/ferramentas'
target.mkdir(parents=True, exist_ok=True)
(target / 'assets').mkdir(exist_ok=True)
(root / 'frontend/public/assets').mkdir(parents=True, exist_ok=True)
for asset in ('jalapao.css', 'custo-3d.js', 'logo-jalapao.svg', 'logo-jalapao.png', 'selo-jalapao.jpg'):
    shutil.copy2(root / 'site/assets' / asset, target / 'assets' / asset)
    if asset.startswith('logo'):
        shutil.copy2(root / 'site/assets' / asset, root / 'frontend/public/assets' / asset)
for name in ('impressao-3d', 'calculadora', 'etiquetas'):
    html = (root / f'site/{name}.html').read_text(encoding='utf-8')
    html = html.replace('href="index.html"', 'href="/jalapao-store"').replace('href="produtos-3d.html"', 'href="/jalapao-store/produtos"')
    if name == 'impressao-3d':
        html = html.replace('<script src="assets/produtos-seed.js"></script>', '').replace('<script src="assets/produtos.js"></script>', '')
        start = html.index('/* ---------- salvar e editar produtos ---------- */')
        end = html.index('</script>', start)
        html = html[:start] + '''
// Persistence now belongs to the authenticated Django API; no local product copies.
let produtoAtual = null;
const campos = {precoKg:'filament_price_kg',gramas:'weight_g',consumo:'power_w',horas:'hours',minutos:'minutes',kwh:'energy_price_kwh',maoDeObra:'labor_cost',custoFixo:'fixed_cost',margem:'markup_percent'};
async function salvarProduto(comoNovo){
  const name=el('nomeProduto').value.trim();
  if(!name){el('nomeProduto').focus();el('estadoSalvamento').textContent='Informe o nome do produto.';return;}
  el('btnSalvar').disabled=true;el('btnSalvarNovo').disabled=true;
  const values=lerEntradas();
  const printing=Object.fromEntries(Object.entries(campos).map(([old,key])=>[key,Number(values[old]||0)]));
  const editing=produtoAtual&&!comoNovo;
  const payload={name,kind:'printing',printing};
  if(!editing)payload.sku='3D-'+crypto.randomUUID().slice(0,12);
  try{
    const response=await fetch('/jalapao-store/api/products'+(editing?'/'+produtoAtual:''),{method:editing?'PATCH':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const result=await response.json();
    if(response.status===401){location.href='/jalapao-store/login';return;}
    if(!response.ok)throw new Error(JSON.stringify(result.errors||result));
    produtoAtual=result.id;el('btnSalvar').textContent='Salvar alterações';el('btnSalvarNovo').classList.remove('oculto');
    el('estadoSalvamento').textContent='Produto salvo no catálogo da loja.';
  }catch(error){el('estadoSalvamento').textContent='Não foi possível salvar: '+error.message;}
  finally{el('btnSalvar').disabled=false;el('btnSalvarNovo').disabled=false;}
}
el('btnSalvar').addEventListener('click',()=>salvarProduto(false));
el('btnSalvarNovo').addEventListener('click',()=>salvarProduto(true));
recuperar();calcular();
''' + html[end:]
    (target / f'{name}.html').write_text(html, encoding='utf-8')
