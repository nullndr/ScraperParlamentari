import csv
import os
import re
from multiprocessing import Pool, Process, Manager
import itertools

import requests
from bs4 import BeautifulSoup

from utils import blue, bold, cyan, red

LAST_LEGISLATURE: int = 18
DEGIGNATED_LEGISLATURE: int = 18
CSV_FILENAME_DEPUTATI: str = "deputati.csv"
CSV_FILENAME_SENATORI: str = "senatori.csv"

def unpack_args(func):
    from functools import wraps
    @wraps(func)
    def wrapper(args):
        if isinstance(args, dict):
            return func(**args)
        else:
            return func(*args)
    return wrapper

def create_csv_file(fileName: str) -> None:
    try:
        with open(fileName, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(("id", "cognome", "nome", "email"))
    except Exception as e:
        print(f"[ ! ] Error: {e}")
        os._exit(1)


def write_csv(fileName: str, rows: list[tuple[str, str, str, str]]) -> None:
    try:
        with open(fileName, "a") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(rows)
    except Exception as e:
        print(f"[ ! ] Error: {e}")
        os._exit(1)

@unpack_args
def process_deputies_by_letter(color, char):

    result: list[tuple[str, int, int, int]] = []
    # Statistiche
    deputies_number: int = 0
    deputies_with_email: int = 0
    deputies_without_email: int = 0

    url = f'https://www.camera.it/leg{DEGIGNATED_LEGISLATURE}/28?lettera={char}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    deputies = soup.find_all("div", {"class": "fn"})

    for deputy in deputies:
        deputies_number += 1

        firstname_lastname = deputy.a.text.split()
        firstname = ' '.join(w for w in firstname_lastname if w.istitle())
        lastname = ' '.join(w for w in firstname_lastname if w.isupper())

        # Ottengo l'id troncando il nome della foto profilo in quanto quello contiene gli zeri di padding mentre quello nel link vero e proprio no
        id = deputy.a["href"][133:139]
        deputy_link = f'https://scrivi.camera.it/scrivi?dest=deputato&id_aul={id}'
        response = requests.get(deputy_link)
        write_to = BeautifulSoup(response.text, 'lxml')

        # Il tag HTML 'title' di questa pagina contiene la parola 'Errore' se il
        # deputato è cessato dal mandato parlamentare. Se invece il deputato è in
        # carica, contiene il suo indirizzo email.
        if 'Errore' in write_to.title.text:
            email = ''
            deputies_with_email += 1
        else:
            email = re.compile(
                '\w+@CAMERA.IT').search(write_to.title.text).group().lower()
            deputies_without_email += 1

        # Stampo in console un deputato alla volta per verificare se lo scraping sta funzionando
        print(f' - {globals()[color](id)}\n\t- {bold(lastname)}\n\t- {bold(firstname)}\n\t- {bold(email)}\n')
        result.append((id, lastname, firstname, email))

    # Preparo una tupla da scrivere nel csv
    return result, deputies_number, deputies_with_email, deputies_without_email


def scrape_deputies(index, return_dict, color):

    rows: list[tuple[str, str, str, str]] = []

    # Statistiche
    deputies_number: int = 0
    deputies_with_email: int = 0
    deputies_without_email: int = 0

    with Pool(processes=64) as pool:
        res = pool.map(process_deputies_by_letter, zip(itertools.repeat(color),list(map(chr, range(97, 123)))))
        for data in res:
            rows.append(data[0])
            deputies_number += data[1]
            deputies_with_email += data[3]
            deputies_without_email += data[2]

    # Riepilogo finale
    #print(f'\nI deputati sono {bold(globals()[color](deputies_number))}, di cui {bold(globals()[color](deputies_with_email))} dotati di indirizzo e-mail perché in carica e {bold(globals()[color](deputies_without_email))} no perché cessati dal mandato parlamentare.')
    
    return_dict[index]=[rows, deputies_number, deputies_with_email, deputies_without_email, color]

@unpack_args
def process_senators_by_letter(color, char):

    result = []
    # Statistiche
    senators_number: int = 0
    senators_with_email: int = 0
    senators_without_email: int = 0

    url = f"https://www.senato.it/leg/{DEGIGNATED_LEGISLATURE}/BGT/Schede/Attsen/Sen{char}.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    senators = soup.find_all("div", {"class": "senatore"})

    for senator in senators:
        senators_number += 1
        elem = senator.select_one(":nth-child(2)").p.a
        lastname, firstname = elem.get_text().split(" ", 1)
        # Ottengo l'id troncando il nome della foto profilo in quanto quello contiene gli zeri di padding mentre quello nel link vero e proprio no
        id = senator.select_one(":nth-child(1)").img["src"][-12:][:-4]
        senator_link = f"https://www.senato.it/leg/{LAST_LEGISLATURE}/BGT/Schede/Attsen/{id}.htm"
        response = requests.get(senator_link)
        write_to = BeautifulSoup(response.text, 'lxml')
        # Se si cerca per a con class cnt_email non si trova nulla perchè è iniettato da un js.
        email = write_to.find_all("ul", {"class": "composizione contatti"})

        # La parte della mail viene iniettata da un js quindi quando lo cerco tramite BeautifulSoup trovo solo il js.
        # Essendo il js "fisso" con solo la parte della mail che cambia, taglio la prima parte sempre uguale, divido il restante per l'apice
        # solo una volta così ad indice 0 ci sarà la mail ed a indice 1 ci sarà il resto dello script.
        # L'if è perchè coloro che non hanno la mail non hanno lo script
        if str(email)[37:43] == "script":
            email = str(email)[124:].split("'", 1)[0]
            senators_with_email += 1
        else:
            email = ""
            senators_without_email += 1

        # Stampo in console un senatore alla volta per verificare se lo scraping sta funzionando
        print(f' - {globals()[color](id)}\n\t- {bold(lastname)}\n\t- {bold(firstname)}\n\t- {bold(email)}\n')
        result.append((id, lastname, firstname, email))

    # Preparo una tupla da scrivere nel csv
    return result, senators_number, senators_with_email, senators_without_email


def scrape_senators(index, return_dict, color):

    rows: list[tuple[str, str, str, str]] = []

    # Statistiche
    senators_number = senators_without_email = senators_with_email = 0

    with Pool(processes=64) as pool:
        res = pool.map(process_senators_by_letter, zip(itertools.repeat(color), list(map(chr, range(97, 123)))))
        for data in res:
            rows += data[0]
            senators_number += data[1]
            senators_without_email += data[3]
            senators_with_email += data[2]
    
    # Riepilogo finale
    #print(f'\nI senatori sono {bold(globals()[color](senators_number))}, di cui {bold(globals()[color](senators_without_email))} dotati di indirizzo e-mail e {bold(globals()[color](senators_with_email))} no.')
    
    return_dict[index]=[rows, senators_number, senators_with_email, senators_without_email, color]


def main() -> None:
    manager = Manager()
    return_dict = manager.dict()
    jobs = []
    
    if DEGIGNATED_LEGISLATURE > 16 and DEGIGNATED_LEGISLATURE <= LAST_LEGISLATURE:

        create_csv_file(f'{DEGIGNATED_LEGISLATURE}_{CSV_FILENAME_DEPUTATI}')
        p1 = Process(target=scrape_deputies, args=("deputati", return_dict, "red"))
        jobs.append(p1)
        p1.start()
        
    if DEGIGNATED_LEGISLATURE > 9 and DEGIGNATED_LEGISLATURE <= LAST_LEGISLATURE:

        create_csv_file(f'{DEGIGNATED_LEGISLATURE}_{CSV_FILENAME_SENATORI}')

        p2 = Process(target=scrape_senators, args=("senatori",return_dict, "cyan"))
        jobs.append(p2)
        p2.start()
       
    for proc in jobs:
        proc.join()

    for value in return_dict:
        write_csv(f'{DEGIGNATED_LEGISLATURE}_{value}.csv', return_dict[value][0])
        # Riepilogo finale
        print(f'\nI {value} sono {bold(globals()[return_dict[value][4]](return_dict[value][1]))}, di cui {bold(globals()[return_dict[value][4]](return_dict[value][2]))} dotati di indirizzo e-mail e {bold(globals()[return_dict[value][4]](return_dict[value][3]))} no.')
    
    

if __name__ == "__main__":
    try:
        print(f'\n{bold(blue("::"))} {bold("Avvio dello script")}\n')
        main()
    except KeyboardInterrupt:
        os._exit(1)
