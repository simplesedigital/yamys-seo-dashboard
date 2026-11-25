import os,json,base64,time,subprocess,urllib.request,sys
PID='482634584'
def token(scope='https://www.googleapis.com/auth/analytics.readonly'):
  d=json.loads(base64.b64decode(os.environ['GA4_SERVICE_ACCOUNT_JSON_B64']))
  b64=lambda x: base64.urlsafe_b64encode(x).rstrip(b'=')
  now=int(time.time())
  h=b64(json.dumps({"alg":"RS256","typ":"JWT"}).encode())
  c=b64(json.dumps({"iss":d['client_email'],"scope":scope,"aud":"https://oauth2.googleapis.com/token","iat":now,"exp":now+3600}).encode())
  import tempfile; fd,k=tempfile.mkstemp(suffix='.pem')
  with os.fdopen(fd,'w') as f: f.write(d['private_key'])
  sig=subprocess.run(['openssl','dgst','-sha256','-sign',k],input=h+b'.'+c,capture_output=True).stdout
  os.remove(k)
  jwt=(h+b'.'+c+b'.'+b64(sig)).decode()
  return json.load(urllib.request.urlopen(urllib.request.Request('https://oauth2.googleapis.com/token',data=f'grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion={jwt}'.encode())))['access_token']
TOK=token()
def report(body):
  r=urllib.request.Request(f'https://analyticsdata.googleapis.com/v1beta/properties/{PID}:runReport',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+TOK,'Content-Type':'application/json'})
  try: j=json.load(urllib.request.urlopen(r))
  except urllib.error.HTTPError as e: print(e.read().decode()); raise
  out=[]
  for row in j.get('rows',[]):
    out.append([v['value'] for v in row.get('dimensionValues',[])]+[v['value'] for v in row['metricValues']])
  return out
