import json
import uuid
import datetime
import os


def parse_kaspersky_entry(entry_text):
    item_data = {}
    lines = entry_text.strip().split('\n')
    
    is_note = False
    is_application = False
    text_content = []
    capturing_text = False
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            clean_key = key.strip()
            
            if clean_key == 'Name':
                item_data['name'] = value.strip()
                is_note = True
            elif clean_key == 'Text' and is_note:
                item_data['text'] = value.strip()
                capturing_text = True
                if value.strip():
                    text_content.append(value.strip())
            elif clean_key == 'Website name':
                item_data['name'] = value.strip()
                item_data['type'] = 'login'
            elif clean_key == 'Website URL':
                item_data['url'] = value.strip()
            elif clean_key == 'Application':
                item_data['name'] = value.strip()
                item_data['type'] = 'login'
                is_application = True
            elif clean_key == 'Login name' and is_application:
                pass
            elif clean_key == 'Login':
                item_data['login'] = value.strip()
            elif clean_key == 'Password':
                item_data['password'] = value.strip()
            elif clean_key == 'Comment':
                item_data['comment'] = value.strip()
        else:
            if capturing_text and is_note:
                text_content.append(line.strip())
    
    if is_note and text_content:
        item_data['text'] = '\n'.join(text_content)
        item_data['type'] = 'note'
    
    return item_data


def convert_to_bitwarden_item(kaspersky_item):
    if not kaspersky_item or 'name' not in kaspersky_item or not kaspersky_item['name']:
        return None

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    
    base_item = {
        "id": str(uuid.uuid4()),
        "organizationId": None,
        "folderId": None,
        "reprompt": 0,
        "name": kaspersky_item.get('name', ''),
        "favorite": False,
        "fields": [],
        "collectionIds": None,
        "passwordHistory": [],
        "creationDate": now_utc,
        "revisionDate": now_utc,
        "deletedDate": None
    }
    
    if kaspersky_item.get('type') == 'note':
        base_item.update({
            "type": 2,
            "notes": kaspersky_item.get('text', ''),
            "secureNote": {
                "type": 0
            }
        })
    else:
        base_item.update({
            "type": 1,
            "notes": kaspersky_item.get('comment', '') or None,
            "login": {
                "uris": [
                    {
                        "match": None,
                        "uri": kaspersky_item.get('url', '')
                    }
                ] if kaspersky_item.get('url') else [],
                "username": kaspersky_item.get('login', ''),
                "password": kaspersky_item.get('password', ''),
                "totp": None
            }
        })
    
    return base_item


def main():
    print("Conversor de senhas Kaspersky (.txt) para Bitwarden (.json)")
    print("="*60)

    try:
        input_file = input("Digite o caminho para o arquivo TXT do Kaspersky: ")
        output_file = input("Digite o nome do arquivo de saída JSON (ex: bitwarden.json): ")

        if not os.path.exists(input_file):
            print(f"\nErro: O arquivo '{input_file}' não foi encontrado.")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        entries = content.split('---')
        if entries:
            entries.pop(0)

        bitwarden_items = []
        for entry in entries:
            if entry.strip():
                kaspersky_data = parse_kaspersky_entry(entry)
                bitwarden_item = convert_to_bitwarden_item(kaspersky_data)
                if bitwarden_item:
                    bitwarden_items.append(bitwarden_item)

        bitwarden_json = {
            "encrypted": False,
            "folders": [],
            "items": bitwarden_items
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(bitwarden_json, f, indent=2, ensure_ascii=False)

        print("\nConversão concluída com sucesso!")
        print(f"Foram processados {len(bitwarden_items)} itens.")
        print(f"Seu arquivo compatível com o Bitwarden foi salvo como: '{output_file}'")
        print("\nAgora você pode importar este arquivo no seu cofre Bitwarden em 'Ferramentas' > 'Importar dados'.")

    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
