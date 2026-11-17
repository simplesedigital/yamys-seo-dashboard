import json,urllib.request
def orders(start,finish):
  out=[];page=1
  while True:
    u=f"https://api.vnda.com.br/api/v2/orders?start={start}&finish={finish}&per_page=100&page={page}"
    j=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'Accept':'application/json'})))
    if not j: break
    out+=j; page+=1
    if len(j)<100: break
  return out
