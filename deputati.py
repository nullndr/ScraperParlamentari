import requests, re, lxml, csv
from bs4 import BeautifulSoup

# Creo il file csv e ci metto le intestazioni
with open('deputati.csv', 'w') as csv_file:
    csv_file.write('id,cognome,nome,email\n')

# Statistiche
n_deputati = con_email = senza_email = 0

# Pagina contenente un menù a tendina con nomi, cognomi e id di tutti i deputati
url_elenco_deputati = 'https://www.camera.it/leg18/28'
r = requests.get(url_elenco_deputati)
soup = BeautifulSoup(r.text, 'lxml')

# Estraggo i deputati dal menù a tendina
deputati = soup.find(id='idPersona').find_all(value=re.compile('\d'))

# Per ciascun deputato ...
for deputato in deputati:
    n_deputati += 1
    # ... estraggo id, nome e cognome dal menù a tendina ...
    id = deputato['value']
    cognome_nome = deputato.text.split()
    nome    = ' '.join(w for w in cognome_nome if w.istitle())
    cognome = ' '.join(w for w in cognome_nome if w.isupper())
    # ... mentre l'indirizzo email è disponibile solo sulla sua pagina personale
    # su scrivi.camera.it, quindi mi tocca aprire tale pagina per ciascun deputato
    url_base = 'https://scrivi.camera.it/scrivi?dest=deputato&id_aul='
    r = requests.get(url_base + id)
    scrivi = BeautifulSoup(r.text, 'lxml')

    # Il tag HTML 'title' di questa pagina contiene la parola 'Errore' se il
    # deputato è cessato dal mandato parlamentare. Se invece il deputato è in
    # carica, contiene il suo indirizzo email.
    if 'Errore' in scrivi.title.text:
        email = ''
        senza_email += 1
    else:
        email = re.compile('\w+@CAMERA.IT').search(scrivi.title.text).group().lower()
        con_email += 1

    # Stampo in console un deputato alla volta per verificare se lo scraping sta funzionando
    print(f'{id:7} {cognome:20} {nome:20} {email}')

    # Preparo una tupla da scrivere nel csv
    riga = (id, cognome, nome, email)

    # La 'appendo' al csv
    with open('deputati.csv', 'a') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(riga)

# Riepilogo finale
print(f'\nI deputati sono {n_deputati}, di cui {con_email} dotati di indirizzo e-mail perché in carica e {senza_email} no perché
cessati dal mandato parlamentare.')
