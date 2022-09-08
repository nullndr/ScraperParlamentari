import csv
import os
import re

import requests
from bs4 import BeautifulSoup

CSV_FILENAME_DEPUTATI: str = "deputati.csv"
CSV_FILENAME_SENATORI: str = "senatori.csv"
# Pagina contenente un menù a tendina con nomi, cognomi e id di tutti i deputati
DEPUTIES_URL = 'https://www.camera.it/leg18/28'


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


def scrape() -> list[tuple[str, str, str, str]]:

    rows: list[tuple[str, str, str, str]] = []
    # Statistiche
    deputies_number = deputies_with_email = deputies_without_email = 0

    r = requests.get(DEPUTIES_URL)
    soup = BeautifulSoup(r.text, 'lxml')

    # Estraggo i deputati dal menù a tendina
    deputies = soup.find(id='idPersona').find_all(value=re.compile('\d'))

    # Per ciascun deputato ...
    for deputy in deputies:
        deputies_number += 1
        # ... estraggo id, nome e cognome dal menù a tendina ...
        id = deputy['value']
        lastname_firstname = deputy.text.split()
        firstname = ' '.join(w for w in lastname_firstname if w.istitle())
        lastname = ' '.join(w for w in lastname_firstname if w.isupper())
        # ... mentre l'indirizzo email è disponibile solo sulla sua pagina personale
        # su scrivi.camera.it, quindi mi tocca aprire tale pagina per ciascun deputato
        url_base = 'https://scrivi.camera.it/scrivi?dest=deputato&id_aul='
        r = requests.get(f"{url_base}{id}")
        writeTo = BeautifulSoup(r.text, 'lxml')

        # Il tag HTML 'title' di questa pagina contiene la parola 'Errore' se il
        # deputato è cessato dal mandato parlamentare. Se invece il deputato è in
        # carica, contiene il suo indirizzo email.
        if 'Errore' in writeTo.title.text:
            email = ''
            deputies_without_email += 1
        else:
            email = re.compile(
                '\w+@CAMERA.IT').search(writeTo.title.text).group().lower()
            deputies_with_email += 1

        # Stampo in console un deputato alla volta per verificare se lo scraping sta funzionando
        print(f'{id:7} {lastname:20} {firstname:20} {email}')

        # Preparo una tupla da scrivere nel csv
        rows.append((id, lastname, firstname, email))

    # Riepilogo finale
    print(f'\nI deputati sono {deputies_number}, di cui {deputies_with_email} dotati di indirizzo e-mail perché in carica e {deputies_without_email} no perché cessati dal mandato parlamentare.')
    return rows

def scrape_senatori():

    rows: list[tuple[str, str, str, str]] = []
    
    char = 'a'
    for i in range(0,28):        
        url = "https://www.senato.it/leg/18/BGT/Schede/Attsen/Sen" + char + ".html"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')

        senatori = soup.find_all("div", {"class": "senatore"})
        
        for senatore in senatori:
            elem = senatore.select_one(":nth-child(2)").p.a
            cognome, nome = elem.get_text().lower().split(" ", 1)
            id = senatore.select_one(":nth-child(1)").img["src"][-12:][:-4]
            link_senatore = "https://www.senato.it/leg/18/BGT/Schede/Attsen/" + id + ".htm"
            r = requests.get(link_senatore)
            writeTo = BeautifulSoup(r.text, 'lxml')
            mail = writeTo.find_all("ul", {"class": "composizione contatti"})

            email = str(mail)[124:].split("'", 1)[0]

            print(f'{id:7} {cognome:20} {nome:20} {email}')

            rows.append((id, cognome, nome, email))

        char = chr(ord(char)+1)

    return rows

def main() -> None:
    create_csv_file(CSV_FILENAME_SENATORI)
    create_csv_file(CSV_FILENAME_DEPUTATI)
    
    rows = scrape_senatori()
    write_csv(CSV_FILENAME_SENATORI, rows)

    rows = scrape()

    write_csv(CSV_FILENAME_DEPUTATI, rows)


if __name__ == "__main__":
    main()
