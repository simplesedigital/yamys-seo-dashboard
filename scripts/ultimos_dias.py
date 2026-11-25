"""Rotina diária: relê os últimos N dias (padrão 3, terminando ontem ou na data dada) e imprime,
para cada dia, a aba, a coluna e os valores das linhas 6 a 62 (GA4 + Vnda + Google Ads).
Uso: python3 scripts/ultimos_dias.py [AAAA-MM-DD_ultimo_dia] [N]
Linhas do Meta (58/60/61) não são tocadas (vêm do CSV enviado pela usuária)."""
import sys,subprocess,json,os
from datetime import date,timedelta,datetime,timezone
MES=['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
def col(i):  # índice 0-based -> letra(s)
  s=''
  i+=1
  while i: i,r=divmod(i-1,26); s=chr(65+r)+s
  return s
hoje_br=(datetime.now(timezone.utc)-timedelta(hours=3)).date()
fim=date.fromisoformat(sys.argv[1]) if len(sys.argv)>1 else hoje_br-timedelta(1)
n=int(sys.argv[2]) if len(sys.argv)>2 else 3
here=os.path.dirname(os.path.abspath(__file__))
for k in range(n-1,-1,-1):
  d=fim-timedelta(k)
  out=subprocess.run([sys.executable,os.path.join(here,'dia_planilha.py'),d.isoformat()],capture_output=True,text=True,timeout=300)
  if out.returncode: print(json.dumps({"data":d.isoformat(),"erro":out.stderr[-500:]},ensure_ascii=False)); continue
  linhas=out.stdout.strip().splitlines()
  info=json.loads(linhas[0]); vals=json.loads(linhas[1])
  aba=f"{MES[d.month-1]}{d.year%100:02d}"; c=col(22+d.day)
  print(json.dumps({"data":d.isoformat(),"aba":aba,"faixa":f"'{aba}'!{c}6:{c}62","ultimo_dia":d==fim,"dia":d.day,"info":info,"values":vals},ensure_ascii=False))
