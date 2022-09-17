
# Web scraper per deputati e senatori della repubblica italiana

## Setup

Installa le dipendenze python con:

```bash
$ pip install -r requirements.txt
```

## Avvio

Esegui:

```bash
$ python main.py
```

Per lanciare lo scraper.

Lo script `main.py` crea, nella sua stessa cartella, il file `deputati.csv`, che contiene, separati da virgole e in questo ordine:
- id del deputato (numero di 5 o 6 cifre)
- COGNOME (tutti in maiuscolo)
- Nome (con le iniziali maiuscole)
- indirizzo e-mail @camera.it

Tali dati sono estratti da https://www.camera.it/leg18/28 e dalle pagine personali dei deputati agli indirizzi https://scrivi.camera.it/scrivi?dest=deputato&id_aul=id dove id è l'id del deputato di cui sopra.

## Docker

Nella repo sono presenti il file `Dockefile` e `docker-compose.yaml` per avviare docker e compose.

```bash
$ docker compose up -d
```

> ⚠️ In base alla versione di `docker` in uso è forse necessario usare il comando `docker-compose up -d`

Con il container in esecuzione è possibile controllare lo stato di avvanzamento con:

```bash
$ docker attach scraper
```
