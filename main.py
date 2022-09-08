import csv
import os
import re

import requests
from bs4 import BeautifulSoup

from multiprocessing import Pool

ULTIMA_LEGISLATURA = "18"

LEGISLATURA_DESIGNATA = "18"
CSV_FILENAME_DEPUTATI: str = "deputati.csv"
CSV_FILENAME_SENATORI: str = "senatori.csv"

# Pagina contenente un menù a tendina con nomi, cognomi e id di tutti i deputati
DEPUTIES_URL = 'https://www.camera.it/leg'+LEGISLATURA_DESIGNATA+'/28'

deputies = []

def create_csv_file(fileName: str) -> None:
    try:
        with open(fileName, "x") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(("id", "cognome", "nome", "email"))
    except:
        print(f"[ ! ] Error creating {fileName}: file already exists")
        os._exit(1)


def write_csv(fileName: str, rows: list[tuple[str, str, str, str]]) -> None:
    with open(fileName, "a") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(rows)


def process_lettera_deputati(char_offset):

    result = []
    # Statistiche
    numero_deputati = deputati_con_mail = deputati_senza_mail = 0

    char = chr(ord('a')+char_offset)
    url = "https://www.camera.it/leg"+LEGISLATURA_DESIGNATA+"/28?lettera=" + char
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')

    deputati = soup.find_all("div", {"class": "fn"})
    
    for deputato in deputati:
        numero_deputati += 1
        
        cognome_nome = deputato.a.text.split()
        nome = ' '.join(w for w in cognome_nome if w.istitle())
        cognome = ' '.join(w for w in cognome_nome if w.isupper())

        # Ottengo l'id troncando il nome della foto profilo in quanto quello contiene gli zeri di padding mentre quello nel link vero e proprio no
        id = deputato.a["href"][133:139]
        link_deputato = 'https://scrivi.camera.it/scrivi?dest=deputato&id_aul=' + id
        r = requests.get(link_deputato)
        writeTo = BeautifulSoup(r.text, 'lxml')
        
        # Il tag HTML 'title' di questa pagina contiene la parola 'Errore' se il
        # deputato è cessato dal mandato parlamentare. Se invece il deputato è in
        # carica, contiene il suo indirizzo email.
        if 'Errore' in writeTo.title.text:
            email = ''
            deputati_con_mail += 1
        else:
            email = re.compile(
                '\w+@CAMERA.IT').search(writeTo.title.text).group().lower()
            deputati_senza_mail += 1

        # Stampo in console un deputato alla volta per verificare se lo scraping sta funzionando
        print(f'{id:7} {cognome:20} {nome:20} {email}')
        result.append((id, cognome, nome, email))
    
    # Preparo una tupla da scrivere nel csv
    return result, numero_deputati, deputati_con_mail, deputati_senza_mail


def scrape_deputati():

    rows: list[tuple[str, str, str, str]] = []

    # Statistiche
    numero_deputati = deputati_con_mail = deputati_senza_mail = 0
    
    with Pool(processes=64) as pool:  
        res = pool.map(process_lettera_deputati, range(0,28))
        print(res)
        for data in res:
            rows += data[0]
            numero_deputati += data[1]
            deputati_con_mail += data[3]
            deputati_senza_mail += data[2]

    # Riepilogo finale
    print(f'\nI deputati sono {numero_deputati}, di cui {deputati_con_mail} dotati di indirizzo e-mail perché in carica e {deputati_senza_mail} no perché cessati dal mandato parlamentare.')
    return rows


def process_lettera_senatori(char_offset):

    result = []
    # Statistiche
    numero_senatori = senatori_con_mail = senatori_senza_mail = 0

    char = chr(ord('a')+char_offset)
    url = "https://www.senato.it/leg/"+LEGISLATURA_DESIGNATA+"/BGT/Schede/Attsen/Sen" + char + ".html"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')

    senatori = soup.find_all("div", {"class": "senatore"})
    
    for senatore in senatori:
        numero_senatori += 1
        elem = senatore.select_one(":nth-child(2)").p.a
        cognome, nome = elem.get_text().split(" ", 1)
        # Ottengo l'id troncando il nome della foto profilo in quanto quello contiene gli zeri di padding mentre quello nel link vero e proprio no
        id = senatore.select_one(":nth-child(1)").img["src"][-12:][:-4]
        link_senatore = "https://www.senato.it/leg/"+ULTIMA_LEGISLATURA+"/BGT/Schede/Attsen/" + id + ".htm"
        r = requests.get(link_senatore)
        writeTo = BeautifulSoup(r.text, 'lxml')
        # Se si cerca per a con class cnt_email non si trova nulla perchè è iniettato da un js.
        mail = writeTo.find_all("ul", {"class": "composizione contatti"})

        # La parte della mail viene iniettata da un js quindi quando lo cerco tramite BeautifulSoup trovo solo il js. 
        # Essendo il js "fisso" con solo la parte della mail che cambia, taglio la prima parte sempre uguale, divido il restante per l'apice
        # solo una volta così ad indice 0 ci sarà la mail ed a indice 1 ci sarà il resto dello script.
        # L'if è perchè coloro che non hanno la mail non hanno lo script
        if(str(mail)[37:43]=="script"):
            email = str(mail)[124:].split("'", 1)[0]
            senatori_con_mail += 1
        else:
            email = ""
            senatori_senza_mail += 1

        # Stampo in console un deputato alla volta per verificare se lo scraping sta funzionando
        print(f'{id:7} {cognome:20} {nome:20} {email}')
        result.append((id, cognome, nome, email))
    
    # Preparo una tupla da scrivere nel csv
    return result, numero_senatori, senatori_con_mail, senatori_senza_mail


def scrape_senatori():

    rows: list[tuple[str, str, str, str]] = []

    # Statistiche
    numero_senatori = senatori_con_mail = senatori_senza_mail = 0
    
    with Pool(processes=64) as pool:  
        res = pool.map(process_lettera_senatori, range(0,28))
        for data in res:
            rows += data[0]
            numero_senatori += data[1]
            senatori_con_mail += data[2]
            senatori_senza_mail += data[3]

    # Riepilogo finale
    print(f'\nI senatori sono {numero_senatori}, di cui {senatori_con_mail} dotati di indirizzo e-mail e {senatori_senza_mail} no.')
    return rows

def main() -> None:
    if (int(LEGISLATURA_DESIGNATA) > 16 and int(LEGISLATURA_DESIGNATA) <= int(ULTIMA_LEGISLATURA)):
        create_csv_file(LEGISLATURA_DESIGNATA + "_" + CSV_FILENAME_DEPUTATI)
        rows = scrape_deputati()
        write_csv(LEGISLATURA_DESIGNATA + "_" + CSV_FILENAME_DEPUTATI, rows)
    '''
    if (int(LEGISLATURA_DESIGNATA) > 9 and int(LEGISLATURA_DESIGNATA) <= int(ULTIMA_LEGISLATURA)):
        create_csv_file(LEGISLATURA_DESIGNATA + "_" + CSV_FILENAME_SENATORI)
        rows = scrape_senatori()
        write_csv(LEGISLATURA_DESIGNATA + "_" + CSV_FILENAME_SENATORI, rows)
    '''

if __name__ == "__main__":
    main()
