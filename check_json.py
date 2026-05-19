import json

with open('investigacion_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('check_output.txt', 'w', encoding='utf-8') as out:
    for k, v in data.items():
        cur_len = len(v['curiosos'])
        faq_len = len(v['faqs'])
        preview = v['curiosos'][:100].replace('\n', ' ')
        out.write(f'{k} | curiosos:{cur_len} | faqs:{faq_len}\n')
        out.write(f'  Preview: {preview}\n\n')

print('OK - ver check_output.txt')
