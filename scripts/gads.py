"""Leitura (somente) do Google Ads da Yamys via conta de serviço (GA4_SERVICE_ACCOUNT_JSON_B64).
MCC 4167830880, conta 7887681642, API v24. Sem developer-token (projeto em nível Exploração)."""
import json,urllib.request,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from ga4 import token
MCC='4167830880'; CID='7887681642'
def search(query):
  tok=token('https://www.googleapis.com/auth/adwords')
  r=urllib.request.Request(f'https://googleads.googleapis.com/v24/customers/{CID}/googleAds:searchStream',
     data=json.dumps({'query':query}).encode(),
     headers={'Authorization':'Bearer '+tok,'login-customer-id':MCC,'Content-Type':'application/json'})
  return [x for ch in json.load(urllib.request.urlopen(r,timeout=90)) for x in ch.get('results',[])]
def dia(D):
  """Totais da conta no dia D (AAAA-MM-DD): cliques, custo (R$), valor de conversão (receita painel)."""
  rows=search(f"SELECT metrics.clicks, metrics.cost_micros, metrics.conversions_value FROM customer WHERE segments.date = '{D}'")
  m=rows[0]['metrics'] if rows else {}
  return int(m.get('clicks',0)), round(int(m.get('costMicros',0))/1e6,2), round(float(m.get('conversionsValue',0)),2)
if __name__=='__main__': print(dia(sys.argv[1]))
