import re
import json

with open('investigacion/ADIS_Investigacion_Productos_Completo.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar categorias
cat_lines = []
for i, line in enumerate(lines):
    if 'CATEGOR' in line.upper() and ':' in line:
        m = re.search(r'(\d+)\s*:\s*(.+)', line)
        if m and i > 30:
            cat_lines.append((i, m.group(1), m.group(2).strip()))

research = {}
for i, (start_idx, num, name) in enumerate(cat_lines):
    end_idx = cat_lines[i+1][0] if i+1 < len(cat_lines) else len(lines)
    body = ''.join(lines[start_idx:end_idx])
    
    # Buscar secciones con ## o ###
    faq_m = re.search(r'(?:##\s*\d+\.?\s*PREGUNTAS FRECUENTES|###\s*\d+\S*\s*PREGUNTAS FRECUENTES)(.*?)(?=##\s*\d+\.?\s|###\s*\d+\S*\s|\Z)', body, re.DOTALL | re.IGNORECASE)
    faqs = faq_m.group(1).strip() if faq_m else ''
    
    cur_m = re.search(r'(?:##\s*\d+\.?\s*DATOS CURIOSOS|###\s*\d+\S*\s*DATOS CURIOSOS)(.*?)(?=##\s*\d+\.?\s|###\s*\d+\S*\s|\Z)', body, re.DOTALL | re.IGNORECASE)
    curiosos = cur_m.group(1).strip() if cur_m else ''
    
    comp_m = re.search(r'(?:##\s*\d+\.?\s*COMPARATIVAS|###\s*\d+\S*\s*COMPARATIVAS)(.*?)(?=##\s*\d+\.?\s|###\s*\d+\S*\s|\Z)', body, re.DOTALL | re.IGNORECASE)
    comparativas = comp_m.group(1).strip() if comp_m else ''
    
    venta_m = re.search(r'(?:##\s*\d+\.?\s*FRASES DE VENTA|###\s*\d+\S*\s*FRASES DE VENTA)(.*?)(?=##\s*\d+\.?\s|###\s*\d+\S*\s|\Z)', body, re.DOTALL | re.IGNORECASE)
    ventas = venta_m.group(1).strip() if venta_m else ''
    
    clean_name = re.sub(r'[^\w\s]', '', name).strip()
    research[clean_name] = {
        'faqs': faqs,
        'curiosos': curiosos,
        'comparativas': comparativas,
        'ventas': ventas,
    }

with open('investigacion_data.json', 'w', encoding='utf-8') as f:
    json.dump(research, f, ensure_ascii=False, indent=2)

print('OK: ' + str(len(research)) + ' categorias')
for k, v in research.items():
    print(k[:35] + ' | FAQ:' + str(len(v['faqs'])) + ' CUR:' + str(len(v['curiosos'])) + ' COMP:' + str(len(v['comparativas'])) + ' VENT:' + str(len(v['ventas'])))
