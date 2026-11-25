"""Puxa GA4 (propriedade 482634584) e Vnda de um dia e imprime a coluna da aba NovXX.
Uso: python3 scripts/dia_planilha.py 2026-11-16
Linhas: 6 sessões, 8 pedidos Vnda, 10 faturamento Vnda, 14-17 sessões Direto/Orgânico/E-mail/Referral+Social,
24-27 receita GA4 dos mesmos canais, 44 sessões google/cpc, 46 cliques Google Ads, 48 custo Google Ads,
50 receita GA4 Google (Paid Search + Cross-network), 56 sessões facebook+Instagram/cpc, 62 receita GA4 Paid Social.
Linhas 46/48/49 (cliques, custo e receita painel do Google Ads) vêm da API do Google Ads (scripts/gads.py);
se ela falhar, 46/48 caem para o GA4 e 49 fica vazia. Linhas 58/60/61 (Meta) vêm do CSV enviado pela usuária."""
import sys,collections,json,os
sys.path.insert(0,os.path.dirname(__file__))
from ga4 import report
from vnda import orders
from datetime import date,timedelta
D=sys.argv[1]; d0=date.fromisoformat(D); dr=[{"startDate":D,"endDate":D}]
tot=report({"dateRanges":dr,"metrics":[{"name":"sessions"}]})[0][0]
c=collections.defaultdict(lambda:[0,0.0])
for k,s,rv in report({"dateRanges":dr,"dimensions":[{"name":"sessionDefaultChannelGroup"}],"metrics":[{"name":"sessions"},{"name":"purchaseRevenue"}]}): c[k]=[int(s),float(rv)]
s=collections.defaultdict(lambda:[0,0.0])
for k,ss,rv in report({"dateRanges":dr,"dimensions":[{"name":"sessionSourceMedium"}],"metrics":[{"name":"sessions"},{"name":"purchaseRevenue"}],"limit":1000}): s[k]=[int(ss),float(rv)]
ads=[0,0.0]
for k,cl,co in report({"dateRanges":dr,"dimensions":[{"name":"sessionSourceMedium"}],"metrics":[{"name":"advertiserAdClicks"},{"name":"advertiserAdCost"}]}):
  if k=='google / cpc': ads=[int(cl),float(co)]
g_painel=None; ads_src='GA4'
try:
  from gads import dia as gads_dia
  ads[0],ads[1],g_painel=gads_dia(D); ads_src='Google Ads API'
except Exception as e: print('AVISO: Google Ads API falhou, usando GA4 para cliques/custo:',e,file=sys.stderr)
n=0; rev=0.0
for o in orders(str(d0-timedelta(1)),str(d0+timedelta(2))):
  if (o.get('received_at') or '')[:10]==D and o['status']=='confirmed': n+=1; rev+=o['total']
r=dict(sess=int(tot),ped=n,fat=round(rev,2),dir=c['Direct'][0],org=c['Organic Search'][0]+c['Organic Shopping'][0],
 mail=sum(v[0] for k,v in s.items() if 'mail' in k.split(' / ')[-1].lower()),ref=c['Referral'][0]+c['Organic Social'][0],
 r_dir=round(c['Direct'][1],2),r_org=round(c['Organic Search'][1]+c['Organic Shopping'][1],2),r_mail=round(c['Email'][1],2),
 r_ref=round(c['Referral'][1]+c['Organic Social'][1],2),g_sess=s['google / cpc'][0],g_cl=ads[0],g_inv=round(ads[1],2),
 g_rev=round(c['Paid Search'][1]+c['Cross-network'][1],2),f_sess=s['facebook / cpc'][0]+s['Instagram / cpc'][0],f_rev=round(c['Paid Social'][1],2),
 unassigned=c['Unassigned'][0],g_painel=g_painel,ads_src=ads_src)
m={6:'sess',8:'ped',10:'fat',14:'dir',15:'org',16:'mail',17:'ref',24:'r_dir',25:'r_org',26:'r_mail',27:'r_ref',44:'g_sess',46:'g_cl',48:'g_inv',49:'g_painel',50:'g_rev',56:'f_sess',62:'f_rev'}
print(json.dumps(r,ensure_ascii=False))
print(json.dumps([[r[m[i]]] if i in m else [None] for i in range(6,63)]))
