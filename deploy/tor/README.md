# Despliegue de Senda como Servicio Oculto Tor (.onion v3)

Este documento detalla la configuración para ofrecer **Senda** dentro de la red Tor de forma anónima, sin intermediarios, sin rastreo y con compatibilidad automática mediante la cabecera estándar `Onion-Location`.

---

## 1. Instalación del servicio Tor

En sistemas Debian / Ubuntu:
```bash
sudo apt update && sudo apt install -y tor
```

En sistemas Gentoo:
```bash
sudo emerge --ask net-vpn/tor
```

En sistemas Arch Linux:
```bash
sudo pacman -S tor
```

---

## 2. Configurar el Servicio Oculto v3

Copia la configuración de `torrc.senda`:
```bash
sudo cp deploy/tor/torrc.senda /etc/tor/torrc.d/senda.conf
# O agrégalo al final de /etc/tor/torrc
```

Asegúrate de que los permisos sean correctos y reinicia el servicio Tor:
```bash
sudo systemctl restart tor
```

Obtén la dirección `.onion` generada criptográficamente:
```bash
sudo cat /var/lib/tor/senda_onion/hostname
# Ejemplo: xyz123...456.onion
```

---

## 3. Habilitar la cabecera `Onion-Location` en Senda

Cuando los usuarios visitan `https://senda.ideh.top` desde el **Tor Browser**, Senda enviará la cabecera `Onion-Location: http://<tu-direccion>.onion`. Esto hará que Tor Browser muestre un botón morado en la barra de direcciones invitando al usuario a saltar a la versión cebolla directamente.

Agrega la variable de entorno a `/etc/systemd/system/senda.service`:
```ini
Environment="SENDA_ONION_HOST=http://tu-direccion.onion"
```

Aplica y reinicia:
```bash
sudo systemctl daemon-reload
sudo systemctl restart senda
```

---

## 4. Rastreo Ético y Anónimo a través de Tor (Opcional)

Si deseas que el crawler de Senda recorra la web o sitios `.onion` a través de un proxy SOCKS5 de Tor:
```bash
export SENDA_CRAWLER_PROXY="socks5://127.0.0.1:9050"
senda crawl-daemon --max-pages 50
```
