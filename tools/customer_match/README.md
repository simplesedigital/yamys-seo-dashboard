# Customer Match (Google Ads) — listas de clientes

Gera, a partir dos pedidos da Vnda, a **Lista A – Nido potencial** usada como indicador de público da PMax Nido.

- **Critério:** pedido confirmado nos últimos 12 meses com qualquer produto exceto linha infantil; sem pedidos de presente; exclui quem já comprou o Nido.
- **Saída:** dois CSVs com e-mail/telefone/nome em SHA-256 (formato Google Ads). **Nunca salve os CSVs dentro do repositório.**

```bash
python3 -I tools/customer_match/build_lists.py --out /caminho/fora/do/repo
```

## Atualização mensal (dia 2 de cada mês)
1. Gerar os arquivos com o comando acima.
2. Google Ads → Ferramentas → Biblioteca compartilhada → Gerenciador de público-alvo → Segmentos.
3. Abrir `CM - Nido Potencial - Compras 12m` → editar lista → **Substituir dados** → enviar `google_customer_match_lista_A_nido.csv`, tipo de arquivo **Com hash**.
4. Se o Google recusar o arquivo completo, usar `..._email_telefone.csv`.
