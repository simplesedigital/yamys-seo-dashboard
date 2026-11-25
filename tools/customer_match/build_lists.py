#!/usr/bin/env python3
"""Gera as listas de Customer Match (Google Ads) a partir dos pedidos da Vnda.

Lista A - "Nido potencial":
  clientes com pedido confirmado nos ultimos 12 meses contendo qualquer
  categoria exceto linha infantil, sem pedidos de presente, excluindo quem
  ja comprou o Nido.

Saida (pasta --out, NUNCA commitar):
  google_customer_match_lista_A_nido.csv               Email, Phone, First Name, Last Name (SHA-256) + Country, Zip
  google_customer_match_lista_A_nido_email_telefone.csv Email, Phone (SHA-256)

A autenticacao da API da Vnda e injetada pelo proxy do ambiente (sem chave no codigo).
Uso: python3 -I tools/customer_match/build_lists.py --out <pasta_fora_do_repo>
"""
import argparse
import collections
import concurrent.futures as cf
import csv
import datetime as dt
import hashlib
import os
import re
import time
import unicodedata

import requests

API = "https://api.vnda.com.br/api/v2"
NIDO_LAUNCH = dt.date(2026, 10, 1)
CA = "/root/.ccr/ca-bundle.crt"

session = requests.Session()
if os.path.exists(CA):
    session.verify = CA


def get(url, params=None, attempts=6):
    for attempt in range(attempts):
        try:
            r = session.get(url, params=params, headers={"Accept": "application/json"}, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            if r.status_code == 429:
                time.sleep(float(r.headers.get("Retry-After") or 10 * (attempt + 1)))
                continue
        except requests.RequestException:
            pass
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"falha ao buscar {url} {params}")


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def category(name):
    n = norm(name)
    if "nido" in n:
        return "nido"
    if any(k in n for k in ["presente", "gift", "vale ", "cartao", "produto teste"]):
        return "ignorar"
    if any(k in n for k in ["mochila infantil", "lancheira", "kit da escola", "volta as aulas",
                            "hora do lanche", "picnic", "frutinhas", "bone infantil", "primeiras aventuras"]):
        return "infantil"
    return "qualifica"


def months(start, end):
    d = start.replace(day=1)
    while d <= end:
        nxt = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        yield d, min(nxt - dt.timedelta(days=1), end)
        d = nxt


def fetch_month(rng):
    start, finish = rng
    out = []
    for page in range(1, 200):
        data = get(f"{API}/orders", {"start": start.isoformat(), "finish": finish.isoformat(),
                                    "per_page": 50, "page": page, "status": "confirmed"}) or []
        out += data
        if len(data) < 50:
            break
    return out


def order_date(o):
    return dt.datetime.fromisoformat((o.get("confirmed_at") or o["received_at"])[:19]).date()


def sha(x):
    return hashlib.sha256(x.encode("utf-8")).hexdigest() if x else ""


def n_email(e):
    e = (e or "").strip().lower()
    if "@" not in e:
        return ""
    user, dom = e.split("@", 1)
    if dom in ("gmail.com", "googlemail.com"):
        user = user.replace(".", "")
    return f"{user}@{dom}"


def n_phone(area, num):
    dg = re.sub(r"\D", "", (area or "") + (num or ""))
    if dg.startswith("55") and len(dg) in (12, 13):
        dg = dg[2:]
    dg = dg.lstrip("0")
    return "+55" + dg if len(dg) in (10, 11) else ""


def n_name(x):
    return re.sub(r"\s+", " ", (x or "").strip().lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--window-days", type=int, default=365)
    args = ap.parse_args()
    if os.path.abspath(args.out).startswith(os.path.abspath(os.path.dirname(__file__) + "/../..")):
        raise SystemExit("--out precisa ficar FORA do repositorio (dados de clientes).")
    os.makedirs(args.out, exist_ok=True)

    today = dt.date.today()
    cutoff = today - dt.timedelta(days=args.window_days)
    start = min(cutoff, NIDO_LAUNCH)

    with cf.ThreadPoolExecutor(6) as ex:
        orders = {o["id"]: o for chunk in ex.map(fetch_month, list(months(start, today))) for o in chunk}
    by = collections.defaultdict(list)
    for o in orders.values():
        em = (o.get("email") or "").strip().lower()
        if em:
            by[em].append(o)

    selected, nido = {}, 0
    for em, lst in by.items():
        if any(category(i["product_name"]) == "nido" for o in lst for i in o["items"]):
            nido += 1
            continue
        ok = [o for o in lst
              if order_date(o) >= cutoff
              and not (o.get("extra") or {}).get("NomeDaPessoa")
              and "qualifica" in {category(i["product_name"]) for i in o["items"]}]
        if ok:
            selected[em] = max(lst, key=order_date)["client_id"]

    def client(cid):
        if not cid:
            return {}
        try:
            return get(f"{API}/clients/{cid}") or {}
        except RuntimeError:
            return None

    with cf.ThreadPoolExecutor(4) as ex:
        clients = dict(zip(selected, ex.map(client, selected.values())))
    for em in [k for k, v in clients.items() if v is None]:  # 2a tentativa, sem paralelismo
        time.sleep(1)
        clients[em] = client(selected[em]) or {}  # sem dados extras, a linha segue so com e-mail

    full, simple, stats = [], [], collections.Counter()
    for em, c in clients.items():
        a = c.get("recent_address") or {}
        e = n_email(em)
        p = n_phone(a.get("first_phone_area"), a.get("first_phone"))
        fn = n_name(c.get("first_name") or a.get("first_name"))
        ln = n_name(c.get("last_name") or a.get("last_name"))
        z = re.sub(r"\D", "", a.get("zip") or "")
        addr = bool(fn and ln and len(z) == 8)
        stats["com_telefone"] += bool(p)
        stats["com_nome_cep"] += addr
        full.append([sha(e), sha(p), sha(fn) if addr else "", sha(ln) if addr else "",
                     "BR" if addr else "", z if addr else ""])
        simple.append([sha(e), sha(p)])

    f1 = os.path.join(args.out, "google_customer_match_lista_A_nido.csv")
    f2 = os.path.join(args.out, "google_customer_match_lista_A_nido_email_telefone.csv")
    with open(f1, "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["Email", "Phone", "First Name", "Last Name", "Country", "Zip"])
        w.writerows(full)
    with open(f2, "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["Email", "Phone"])
        w.writerows(simple)

    print(f"pedidos lidos: {len(orders)} | periodo: {start} a {today} | janela desde {cutoff}")
    print(f"Lista A: {len(full)} clientes | excluidas (ja compraram Nido): {nido} | {dict(stats)}")
    print(f1)
    print(f2)


if __name__ == "__main__":
    main()
