# -*- coding: utf-8 -*-
from pathlib import Path

fp = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina\generar_web.py')
content = fp.read_text(encoding='utf-8')

old_chatbot = '''    // Chatbot
    (function() {
      const chatWindow = document.getElementById('chatbotWindow');
      const chatBody = document.getElementById('chatbotBody');
      
      window.toggleChat = function() {
        chatWindow.classList.toggle('active');
        if (chatWindow.classList.contains('active') && chatBody.children.length === 0) {
          showWelcome();
        }
      };
      
      function addMessage(text, isUser) {
        const msg = document.createElement('div');
        msg.className = 'chat-message ' + (isUser ? 'user' : 'bot');
        msg.innerHTML = text;
        chatBody.appendChild(msg);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      function showOptions() {
        const existing = chatBody.querySelector('.chat-options');
        if (existing) existing.remove();
        
        const opts = document.createElement('div');
        opts.className = 'chat-options';
        opts.innerHTML = `
          <button class="chat-option-btn" onclick="chatOption('ubicacion')">📍 Ubicación</button>
          <button class="chat-option-btn" onclick="chatOption('fichas')">📋 Fichas técnicas</button>
          <button class="chat-option-btn" onclick="chatOption('venta')">📦 ¿Cómo se venden?</button>
          <button class="chat-option-btn" onclick="chatOption('precios')">💰 Precios</button>
          <button class="chat-option-btn" onclick="chatOption('whatsapp')">💬 Hablar con asesor</button>
        `;
        chatBody.appendChild(opts);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      window.chatOption = function(key) {
        const existing = chatBody.querySelector('.chat-options');
        if (existing) existing.remove();
        
        const responses = {
          ubicacion: `📍 <strong>Nogales, Sonora</strong> y atendemos también en <strong>Rio Rico, AZ</strong>.<br><br>Puedes ver nuestra ubicación exacta en la página de <a href="contacto.html" style="color:#C5A059">Contacto</a> o en <a href="https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8" target="_blank" style="color:#C5A059">Google Maps →</a>`,
          fichas: `📋 Cada producto tiene su ficha técnica disponible.<br><br>Ve al <a href="index.html#categorias" style="color:#C5A059">Catálogo</a>, selecciona la categoría y subcategoría que te interesa, y haz clic en <strong>"Ver Ficha Técnica"</strong>.`,
          venta: `📦 Vendemos por pieza, caja o metro cuadrado según el producto.<br><br>Usa la <strong>calculadora de materiales</strong> en cada categoría para saber cuánto necesitas, o solicita una <strong>cotización</strong> directamente desde cualquier producto.`,
          precios: `💰 Los precios varían según el producto y la cantidad.<br><br>¿Te gustaría que un asesor te prepare una cotización personalizada?<br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20una%20cotización" target="_blank" class="chat-whatsapp-btn">📱 Solicitar cotización</a>`,
          whatsapp: `💬 Te conecto con un asesor por WhatsApp...`
        };
        
        const labels = {
          ubicacion: '📍 Ubicación',
          fichas: '📋 Fichas técnicas',
          venta: '📦 ¿Cómo se venden?',
          precios: '💰 Precios',
          whatsapp: '💬 Hablar con asesor'
        };
        
        addMessage(labels[key], true);
        
        if (key === 'whatsapp') {
          setTimeout(() => {
            window.open('https://wa.me/526311928993?text=Hola%20ADIS,%20tengo%20una%20pregunta', '_blank');
            addMessage('✅ Se abrió WhatsApp. Un asesor te atenderá pronto.', false);
            setTimeout(showOptions, 1000);
          }, 500);
        } else {
          setTimeout(() => {
            addMessage(responses[key], false);
            setTimeout(showOptions, 500);
          }, 400);
        }
      };
      
      function showWelcome() {
        addMessage('¡Hola! 👋 Soy el <strong>asistente virtual de ADIS</strong>.<br>¿En qué puedo ayudarte hoy?', false);
        setTimeout(showOptions, 300);
      }
    })();'''

new_chatbot = '''    // Chatbot Inteligente v2
    (function() {
      const chatWindow = document.getElementById('chatbotWindow');
      const chatBody = document.getElementById('chatbotBody');
      let allProducts = [];
      let kb = {
        horarios: {
          lunes: 'Cerrado 🚪',
          martes: '10:00 a 19:00',
          miercoles: '9:00 a 19:00',
          jueves: '9:00 a 19:00',
          viernes: '9:00 a 19:00',
          sabado: '9:00 a 19:00',
          domingo: '9:00 a 15:00'
        },
        contacto: {
          whatsapp: '+52 631-192-8993',
          tel_showroom: '+52 631-120-4943',
          email: 'adis.remodelacion@gmail.com',
          ubicacion: 'Nogales, Sonora y Rio Rico, AZ'
        }
      };
      
      fetch('products.json')
        .then(r => r.json())
        .then(data => { allProducts = data; })
        .catch(() => { allProducts = []; });
      
      window.toggleChat = function() {
        chatWindow.classList.toggle('active');
        if (chatWindow.classList.contains('active') && chatBody.children.length === 0) {
          showWelcome();
        }
      };
      
      function addMessage(text, isUser) {
        const msg = document.createElement('div');
        msg.className = 'chat-message ' + (isUser ? 'user' : 'bot');
        msg.innerHTML = text;
        chatBody.appendChild(msg);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      function removeInputs() {
        const existing = chatBody.querySelector('.chat-input-wrap');
        if (existing) existing.remove();
      }
      
      function showQuickReplies(replies) {
        const existing = chatBody.querySelector('.chat-options');
        if (existing) existing.remove();
        const opts = document.createElement('div');
        opts.className = 'chat-options';
        opts.innerHTML = replies.map(r => `<button class="chat-option-btn" onclick="chatBotProcess('${r.replace(/'/g, "\\'")}')">${r}</button>`).join('');
        chatBody.appendChild(opts);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      function addInputField() {
        removeInputs();
        const wrap = document.createElement('div');
        wrap.className = 'chat-input-wrap';
        wrap.style.cssText = 'display:flex;gap:0.5rem;margin-top:0.5rem;padding-top:0.5rem;border-top:1px solid rgba(197,160,89,0.15);';
        wrap.innerHTML = `<input type="text" id="chatTextInput" placeholder="Escribe tu pregunta..." autocomplete="off" style="flex:1;padding:0.6rem 1rem;background:rgba(255,255,255,0.06);border:1px solid rgba(197,160,89,0.25);border-radius:20px;color:var(--light);font-family:'Montserrat',sans-serif;font-size:0.82rem;" onkeydown="if(event.key==='Enter'){chatBotProcess(this.value);this.value='';}"><button onclick="chatBotProcess(document.getElementById('chatTextInput').value);document.getElementById('chatTextInput').value='';" style="background:var(--gold);border:none;border-radius:50%;width:34px;height:34px;cursor:pointer;color:var(--black);font-size:0.9rem;flex-shrink:0;">➤</button>`;
        chatBody.appendChild(wrap);
        chatBody.scrollTop = chatBody.scrollHeight;
        setTimeout(() => { const inp = document.getElementById('chatTextInput'); if (inp) inp.focus(); }, 100);
      }
      
      window.chatBotProcess = function(rawText) {
        if (!rawText || !rawText.trim()) return;
        const text = rawText.trim();
        addMessage(text, true);
        removeInputs();
        
        const q = text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        const response = findResponse(q, text);
        
        setTimeout(() => {
          addMessage(response, false);
          showQuickReplies(['Ver productos', 'Horarios', 'Cotización', 'Ubicación', 'Hablar con asesor']);
          addInputField();
        }, 500);
      };
      
      function findResponse(q, original) {
        // SALUDO
        if (/^(hola|buenas|buenos|hey|hi|hello|que tal|q tal)/.test(q)) {
          return '¡Hola! 👋 Bienvenido a <strong>ADIS Diseño & Remodelación</strong>. Soy tu asistente virtual y puedo ayudarte con:<br><br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios de atención 🕐<br>• Ubicación y envíos 📍<br>• Información técnica 📋<br><br>¿Qué necesitas? Escribe tu pregunta o usa los botones de abajo.';
        }
        
        // HORARIOS
        if (q.includes('horario') || q.includes('hora') || q.includes('abierto') || q.includes('atencion') || q.includes('cierran') || q.includes('abren')) {
          let r = '🕐 <strong>Nuestros horarios de atención:</strong><br><br>';
          r += '• <strong>Lunes:</strong> ' + kb.horarios.lunes + '<br>';
          r += '• <strong>Martes:</strong> ' + kb.horarios.martes + '<br>';
          r += '• <strong>Miércoles:</strong> ' + kb.horarios.miercoles + '<br>';
          r += '• <strong>Jueves:</strong> ' + kb.horarios.jueves + '<br>';
          r += '• <strong>Viernes:</strong> ' + kb.horarios.viernes + '<br>';
          r += '• <strong>Sábado:</strong> ' + kb.horarios.sabado + '<br>';
          r += '• <strong>Domingo:</strong> ' + kb.horarios.domingo + '<br><br>';
          r += '💬 <strong>WhatsApp:</strong> Respondemos de lunes a sábado hasta las 20:00 hrs.';
          return r;
        }
        if (q.includes('lunes')) return 'Los <strong>lunes</strong> estamos <strong>cerrados</strong> 🚪. Te atendemos de martes a domingo con horarios variados. ¿Te gustaría saber el horario de algún otro día?';
        if (q.includes('domingo')) return 'Los <strong>domingos</strong> abrimos de <strong>9:00 a 15:00</strong> ☀️. Es un buen día para venir a conocer nuestros productos sin prisa.';
        if (q.includes('sabado')) return 'Los <strong>sábados</strong> atendemos de <strong>9:00 a 19:00</strong> 💪. Es nuestro día con más afluencia, te recomiendo venir temprano.';
        
        // CONTACTO / WHATSAPP / TELEFONO
        if (q.includes('whatsapp') || q.includes('telefono') || q.includes('celular') || q.includes('numero') || q.includes('llamar') || q.includes('contacto') || q.includes('hablar')) {
          return '📱 <strong>Contactos directos:</strong><br><br>• <strong>WhatsApp:</strong> ' + kb.contacto.whatsapp + '<br>• <strong>Showroom:</strong> ' + kb.contacto.tel_showroom + '<br>• <strong>Email:</strong> ' + kb.contacto.email + '<br><br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20tengo%20una%20pregunta" target="_blank" class="chat-whatsapp-btn">💬 Abrir WhatsApp</a>';
        }
        
        // UBICACION
        if (q.includes('ubicacion') || q.includes('donde') || q.includes('direccion') || q.includes('ubicados') || q.includes('local') || q.includes('tienda') || q.includes('showroom') || q.includes('nogales') || q.includes('rio rico')) {
          return '📍 <strong>Ubicación:</strong><br><br>Atendemos en <strong>Nogales, Sonora</strong> y <strong>Rio Rico, AZ</strong>.<br><br>📌 Puedes ver la dirección exacta y el mapa en nuestra página de <a href="contacto.html" style="color:#C5A059">Contacto</a> o en <a href="https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8" target="_blank" style="color:#C5A059">Google Maps →</a><br><br>🏠 ¡Tenemos showroom! Puedes venir a ver y tocar los materiales antes de comprar.';
        }
        
        // PRECIOS / COTIZACION
        if (q.includes('precio') || q.includes('cuesta') || q.includes('cuanto') || q.includes('valor') || q.includes('cotizacion') || q.includes('cotizar') || q.includes('presupuesto')) {
          return '💰 <strong>Precios:</strong><br><br>Los precios varían según el producto, cantidad y zona de entrega. Vendemos por pieza, caja o metro cuadrado según la categoría.<br><br>✅ La mejor forma de saber el precio exacto es solicitando una <strong>cotización personalizada</strong>. Es gratis y te respondemos el mismo día.<br><br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20una%20cotización" target="_blank" class="chat-whatsapp-btn">📱 Solicitar cotización gratis</a>';
        }
        
        // ENVIO / ENTREGA
        if (q.includes('envio') || q.includes('entrega') || q.includes('mandan') || q.includes('envian') || q.includes('domicilio') || q.includes('llevan')) {
          return '🚚 <strong>Envíos y entregas:</strong><br><br>Realizamos entregas a domicilio. El costo y tiempo depende de la zona y el volumen del pedido.<br><br>📦 Para cotizar el envío, envíanos tu dirección por WhatsApp con los productos que necesitas.<br><br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20cotizar%20un%20envío" target="_blank" class="chat-whatsapp-btn">📱 Cotizar envío</a>';
        }
        
        // INSTALACION
        if (q.includes('instalacion') || q.includes('instalan') || q.includes('colocan') || q.includes('ponen') || q.includes('colocacion')) {
          return '🛠️ <strong>Servicio de instalación:</strong><br><br>Sí contamos con equipo de instalación profesional. El costo se cotiza aparte según el tipo de trabajo, metros cuadrados y ubicación.<br><br>✅ También vendemos materiales sueltos si prefieres instalar por tu cuenta.<br><br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20cotizar%20instalación" target="_blank" class="chat-whatsapp-btn">📱 Cotizar instalación</a>';
        }
        
        // PAGO / FORMAS DE PAGO
        if (q.includes('pago') || q.includes('pagos') || q.includes('tarjeta') || q.includes('credito') || q.includes('efectivo') || q.includes('transferencia') || q.includes('meses')) {
          return '💳 <strong>Formas de pago:</strong><br><br>• Efectivo 💵<br>• Transferencia bancaria 🏦<br>• Depósito 📥<br>• Tarjetas de crédito/débito 💳<br><br>Para pedidos grandes podemos manejar pagos a convenir. Escríbenos para más detalles.<br><br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20pregunto%20por%20formas%20de%20pago" target="_blank" class="chat-whatsapp-btn">📱 Preguntar por pagos</a>';
        }
        
        // GARANTIA
        if (q.includes('garantia') || q.includes('garantiza')) {
          return '✅ <strong>Garantía:</strong><br><br>La mayoría de nuestros productos cuentan con garantía del fabricante. El tiempo varía según el material:<br><br>• Placas PVC: 15 años<br>• Lambrín WPC: 15 años<br>• Pisos SPC: 12 años (residencial)<br>• Zacate sintético: 5 años<br><br>La garantía cubre defectos de fábrica. Para hacerla válida conserva tu ticket de compra.';
        }
        
        // PRODUCTOS / CATALOGO / MATERIALES
        if (q.includes('producto') || q.includes('catalogo') || q.includes('materiales') || q.includes('que venden') || q.includes('tienen') || q.includes('ofrecen')) {
          return '📦 <strong>Nuestros productos:</strong><br><br>• Placas PVC (tipo madera, texturizadas, espejo)<br>• Lambrín WPC (interior y exterior)<br>• Paneles 3D decorativos<br>• Pisos (Laminado, WPC, SPC, Deck)<br>• Plafón PVC<br>• Vigas PVC<br>• Zacate sintético y follaje<br>• Cladding y revestimientos<br><br>👉 <a href="index.html#categorias" style="color:#C5A059">Ver catálogo completo</a>';
        }
        
        // DIFERENCIAS ENTRE MATERIALES
        if (q.includes('wpc') && (q.includes('pvc') || q.includes('diferencia'))) {
          return '🆚 <strong>WPC vs PVC:</strong><br><br><strong>WPC (Wood Plastic Composite):</strong><br>• Mezcla de madera y plástico<br>• Aspecto más natural tipo madera real<br>• Ideal para exteriores (resistente a UV y lluvia)<br>• Más pesado y robusto<br><br><strong>PVC:</strong><br>• Plástico 100%<br>• Más ligero y fácil de instalar<br>• Ideal para interiores<br>• Mayor variedad de diseños (madera, espejo, textura)<br><br>¿Te ayudo a elegir según tu proyecto? 💬';
        }
        if (q.includes('spc') && (q.includes('wpc') || q.includes('diferencia') || q.includes('pvc'))) {
          return '🆚 <strong>SPC vs WPC vs Laminado:</strong><br><br><strong>SPC (Stone Plastic Composite):</strong><br>• Muy resistente al agua 💧<br>• Ideal para cocinas y baños<br>• Instalación rápida tipo click<br><br><strong>WPC:</strong><br>• Más cálido y confortable al caminar<br>• Buen aislamiento térmico y acústico<br>• Ideal para recámaras y salas<br><br><strong>Laminado:</strong><br>• Más económico<br>• Recomendado para áreas de bajo tráfico<br><br>¿Para qué espacio es? Te recomiendo el mejor.';
        }
        
        // BUSQUEDA DE PRODUCTOS POR NOMBRE
        if (allProducts.length > 0) {
          const terms = q.split(/\\s+/).filter(t => t.length > 2);
          const matches = allProducts.filter(p => {
            const text = (p.name + ' ' + p.category + ' ' + (p.subcategory || '')).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
            return terms.some(t => text.includes(t));
          }).slice(0, 3);
          
          if (matches.length > 0) {
            let r = '🔎 <strong>Encontré estos productos:</strong><br><br>';
            matches.forEach(m => {
              r += `<div style="display:flex;gap:0.6rem;align-items:center;margin-bottom:0.6rem;padding:0.5rem;background:rgba(197,160,89,0.08);border-radius:8px;"><img src="${m.thumb}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;border:1px solid rgba(197,160,89,0.2);"><div><a href="${m.url}" style="color:#C5A059;font-weight:600;font-size:0.85rem;">${m.name}</a><div style="font-size:0.72rem;color:rgba(245,245,245,0.5);">${m.category}${m.subcategory ? ' / ' + m.subcategory : ''}</div></div></div>`;
            });
            r += '<br>¿Quieres que te ayude con algo específico de estos productos?';
            return r;
          }
        }
        
        // AGRADECIMIENTO / DESPEDIDA
        if (q.includes('gracias') || q.includes('thank') || q.includes('perfecto') || q.includes('excelente')) {
          return '¡Con mucho gusto! 😊🙌 Estoy aquí para lo que necesites. Si tienes más dudas, escríbenos por WhatsApp al <strong>' + kb.contacto.whatsapp + '</strong> o visítanos en el showroom. ¡Que tengas un excelente día!';
        }
        if (q.includes('adios') || q.includes('bye') || q.includes('hasta luego') || q.includes('nos vemos')) {
          return '¡Hasta luego! 👋 Gracias por contactar a ADIS Diseño & Remodelación. Recuerda que puedes volver cuando quieras o escribirnos al WhatsApp. ¡Éxito con tu proyecto! 🏠✨';
        }
        
        // DEFAULT
        return 'Disculpa, no entendí muy bien. 😅 Puedo ayudarte con:<br><br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios de atención 🕐<br>• Ubicación y envíos 📍<br>• Formas de pago 💳<br>• Instalación 🛠️<br><br>Escribe tu pregunta o usa los botones de abajo.';
      }
      
      function showWelcome() {
        addMessage('¡Hola! 👋 Bienvenido a <strong>ADIS Diseño & Remodelación</strong>.<br><br>Soy tu asistente virtual y puedo ayudarte con información sobre nuestros productos, horarios, precios, cotizaciones y más.<br><br>¿Qué necesitas? Escribe tu pregunta 👇', false);
        showQuickReplies(['Ver productos', 'Horarios', 'Cotización', 'Ubicación', '¿Tienen envío?']);
        addInputField();
      }
    })();'''

if old_chatbot in content:
    content = content.replace(old_chatbot, new_chatbot)
    fp.write_text(content, encoding='utf-8')
    print("Chatbot actualizado exitosamente")
else:
    print("No se encontró el chatbot antiguo")
