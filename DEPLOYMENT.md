# Despliegue

homepanel corre en una **LXC dedicada en Proxmox**, no como stack de Portainer en
`docker-host`. Es deliberado: este dashboard agrega datos de n8n, Proxmox, Vikunja
y demás, así que si viviera en `docker-host` se caería junto con Docker — justo
cuando más falta haría. Ver [decisión completa](README.md#despliegue).

Actualización automática: un timer de systemd en la propia LXC hace `git fetch`
cada 5 minutos y, si `main` avanzó, hace `pull` + reinstala dependencias +
reinicia el servicio. No requiere abrir ningún puerto de entrada ni mantener un
runner: la LXC solo hace peticiones salientes a GitHub.

## 1. Crear la LXC en Proxmox

- Plantilla Debian 12 (minimal), sin privilegios.
- 1 vCPU / 512&nbsp;MB RAM / 4&nbsp;GB disco son de sobra para esta app.
- IP fija en la LAN (reserva DHCP o estática), para poder apuntar el navegador
  del PC a `http://<ip-lxc>:8000` de forma estable.

## 2. Preparar el sistema (dentro de la LXC, como root)

```bash
apt update && apt install -y python3-venv python3-pip git

useradd -r -m -d /opt/homepanel -s /usr/sbin/nologin homepanel

git clone https://github.com/gomila17/homepanel.git /opt/homepanel
chown -R homepanel:homepanel /opt/homepanel

su -s /bin/bash homepanel -c "
  cd /opt/homepanel &&
  python3 -m venv .venv &&
  .venv/bin/pip install -r requirements.txt
"
```

## 3. Configurar credenciales

```bash
cd /opt/homepanel
cp .env.example .env
nano .env   # rellenar con las credenciales reales (nunca se commitean)
chown homepanel:homepanel .env
chmod 600 .env
```

## 4. Instalar los servicios de systemd

```bash
cd /opt/homepanel
chmod +x deploy/homepanel-update.sh
cp deploy/homepanel.service deploy/homepanel-update.service deploy/homepanel-update.timer \
  /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now homepanel
systemctl enable --now homepanel-update.timer
```

## 5. Verificar

```bash
curl http://127.0.0.1:8000/healthz
systemctl status homepanel
journalctl -u homepanel -f          # logs de la app
journalctl -u homepanel-update -f   # logs de cada comprobación de updates
```

Desde el PC: abrir `http://<ip-lxc>:8000` y, si se quiere como página de
inicio del navegador, configurarla en Ajustes → Al iniciar → Abrir una
página específica.

## Notas

- **Sin HTTPS ni dominio propio**: vive solo en la LAN, como el resto de
  accesos de [LAN ACCESS](README.md). Si más adelante se quiere un nombre
  tipo `panel.gomila.dev`, se puede añadir un host en Nginx Proxy Manager
  igual que con el resto de servicios.
- **Rollback**: al ser solo `git` + `systemd`, revertir es
  `git checkout <commit> && systemctl restart homepanel`. Además, conviene
  tomar una snapshot de Proxmox de la LXC antes de cambios grandes (viene
  gratis con el propio Proxmox).
- **Logs**: los gestiona `journald`, no hace falta configurar rotación aparte.
- **`homepanel-update.service` corre como root** (a diferencia de la app,
  que corre como el usuario sin privilegios `homepanel`) porque necesita
  llamar a `systemctl restart`. Es una LXC de un único propósito, así que
  el compromiso está documentado en `deploy/homepanel-update.service` en
  vez de complicar el setup con una regla de `sudoers`.
- **`fatal: detected dubious ownership in repository`** en
  `journalctl -u homepanel-update`: root ejecutando `git` sobre un
  directorio que no es suyo (`/opt/homepanel` es de `homepanel:homepanel`)
  dispara la protección `safe.directory` de git. `homepanel-update.sh` ya
  lo evita pasando `-c safe.directory=/opt/homepanel` en cada invocación,
  pero si aparece en una LXC con una versión anterior del script, arréglalo
  a mano una vez con `git config --global --add safe.directory /opt/homepanel`
  (como root) y el timer se recupera solo en el siguiente ciclo.
