import json
from queries.halakhot_queries import HalakhotQueries
from services.api_openai.openai_requests import OpenaiRequests
from services.api_notion.notion_requests import NotionRequests


def process_hks_to_openai(file_path):
    text_hk = """
Peut on réciter la bénédiction de netilat yadaim du matin apres avoir essuyé ses mains ?  [Voir uniquement la conclusion pour ceux qui n'ont pas plus de 7s].  • Le _Rambam (Chout peer ador chap 104)_ tranche que ceux qui récitent la bénédiction netilat yadaim à la synagogue prononcent une bénédiction en vain, car il faut que cette dernière soit recitée avant la mitsva (=le lavage des mains par le keli, et donc tout au moins avant l'essuyage). • Le _Maharam mirottenbourg_ ( _Sefer atchbets chap 217_) lui dit que l'usage est de réciter cette bénédiction à la synagogue, et ainsi pensent de nombreux richonim ( _Orhot haim, Kol bo, Tour, Agour, Smak_...).  • Le _Choulhan Aroukh OH 6-2_ dit que "Certains ont l'usage de réciter la bénédiction netilat yadaim à la synagogue, suivie des bénédictions du matin, mais les sefarades n'ont pas cet usage". => Il ressort que le _Choulhan Aroukh_ rejette de réciter la bénédiction apres la mitsva, seulement car ce n'est pas son minhag mais par car ce serait une bénédiction en vain. Cela comme il ressort du _Bet yossef_ qui justifie par : >Avis du _Mahari abouav_ que les sages n'ont pas voulu faire de différence entre les bénédictions du matin et de netilat yadaim, et à ce titre la bénédiction de netilat yadaim serait comme un remerciement dHachem de nous sanctifier et pas une comme une bénédiction de mitsva ( _Tchouvat arachba chap 191_). >Avis de _tossfot (Pessahim 7b "tevila")_ car nos sages n'ont pas fait de différence entre la bénédiction d' "Acher yatsar" apres les toilettes (qui peut etre recitée apres l'essuyage des mains) et "al netilat yadaim" du matin. >Avis du _Maharam halwa (pessahim 7b)_ que la bénédiction "al netilat yadaim" est une bénédiction de louange au même titre que celles du matin, qu'on doit réciter dans tous les cas, pour remercier le créateur.  • En pratique, certains décisionnaires disent qu'on devra reciter la bénédiction avant l'essuyage ( _Kaf Hahayim 4-15, Ben ich hay Toldot 5, et ainsi serait l'avis du Ari Zal et Rachach_).  • Selon d'autres, on ne récitera qu’après l'essuyage, apres avoir retiré tout l'esprit d'impurete ( _Hida Mahazik braha 4-1, Kaf Hahayim falagi 8-6, Kitsour achla 63b_...).  • En conclusion, à priori on recitera la benediction avant l'essuyage, mais si on n'a pas pu avant ou oublier, on pourra la réciter après le plus tot possible, mais pas plus tard qu'après la Amida auquel cas on ne pourra plus ( _Halakha broura t1 p57_, _Chout otsrot yossef chap 7, Piske tchouvot t1 p39_, _Yalkout yossef achkamat aboker p341, et tel qu'il ressort du _Michna broura 4-2, 6-8,9_ que le problème principal de retarder la bénédiction est de creer une interruption)."""
    result_ai = send_to_openai(text_hk)
    result_ai["content"] = text_hk
    page_number = int(input("Entrez le numéro de la page à créer : "))
    while page_number < 0 :
        print("Veuillez entrer un nombre supérieur à 0.")
        page_number = int(input("Entrez le numéro de la page à créer : "))
    notion = NotionRequests()
    notion.create_page(page_number, result_ai)

    # hks_json = load_json_file(file_path)
    page_number = 0
    for hk_text in hks_json[198:]:
        result_ai = send_to_openai(hk_text["halakha"])
        result_ai["content"] = hk_text["halakha"]
        while page_number < 0 :
            print("Veuillez entrer un nombre supérieur à 0.")
            page_number = int(input("Entrez le numéro de la page à créer : "))
        notion = NotionRequests()
        try:
            response = notion.create_page(page_number, result_ai)
            print("Page créée :", response)
        except Exception as e:
            print(f"Erreur lors de l'insertion dans Notion : {e}")
        # break
        # hk_db = save_to_db(result_ai, text_hk)
        page_number += 1

    return True

def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            hks_json = json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    return hks_json

def send_to_openai(hk_text):
    try:
        openai_requests = OpenaiRequests()

        response_json = openai_requests.query_assistant_json(hk_text)
        # response_json["prompt_dallE"] = openai_requests.generate_prompt_dallE(response_json["question"])
        # url_image = openai_requests.generate_image("Peut-on se déplacer dans le domaine public avec un aliment en bouche le Shabbat ?")
        # response_json["image_url"] = url_image
        response_json["text_post"] = openai_requests.generate_text_post(response_json["answer"])
        response_json["legend"] = openai_requests.generate_legend_post(hk_text)
    except Exception as e:
        print(f"Error saving halakha: {e}")
        raise
    return response_json

def save_to_db(result_ai, hk_text):
    try:
        halakha_queries = HalakhotQueries()
        halakha_queries.save_full_halakha(result_ai, hk_text)
    except Exception as e:
        print(f"Error saving halakha: {e}")
        raise

def read_table_notion():
    notion = NotionRequests()
    try:
        data = notion.query_database()
        print(data)
    except Exception as e:
        print(f"Erreur lors de la lecture de la base de données Notion : {e}")

