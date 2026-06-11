import glob

old_tag = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-7NM62QERY3"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-7NM62QERY3');
</script>"""

new_tag = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-6DL4217NSC"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-6DL4217NSC');
</script>"""

files = glob.glob('*.html')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()

    if old_tag in content:
        content = content.replace(old_tag, new_tag)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'REEMPLAZADO: {f}')
    elif 'G-6DL4217NSC' in content:
        print(f'YA TIENE EL NUEVO: {f}')
    else:
        # Si no tiene el tag viejo ni el nuevo, insertamos el nuevo antes de </head>
        if '</head>' in content:
            content = content.replace('</head>', new_tag + '\n</head>')
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f'INSERTADO: {f}')
        else:
            print(f'NO TIENE </head>: {f}')
