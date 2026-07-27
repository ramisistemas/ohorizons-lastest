# Cómo levantar Backstage en local

Guía rápida y autocontenida para arrancar el Backstage de este repo (`~/projects/ohorizons-lastest/backstage`) en la máquina local.

## Prerrequisitos
- **Node 22** instalado vía `nvm` — el Node global del sistema (v25) no es compatible con Backstage.
- Archivo `~/projects/ohorizons-lastest/backstage/.env` con las credenciales de la OAuth App de GitHub y demás variables de entorno (está gitignored, no se versiona).
- Dependencias ya instaladas (`node_modules` presente). Si es la primera vez en esta copia del repo: `yarn install` antes de `yarn start`.

## Puertos
| Servicio | Puerto | URL |
|---|---|---|
| Frontend | 3001 | http://localhost:3001 |
| Backend | 7007 | http://localhost:7007 |

## Arrancar

```bash
cd ~/projects/ohorizons-lastest/backstage
source ~/.nvm/nvm.sh && nvm use 22
set -a && source .env && set +a
yarn start
```

Esto queda corriendo en primer plano. Si lo necesitás en background:

```bash
cd ~/projects/ohorizons-lastest/backstage
source ~/.nvm/nvm.sh && nvm use 22
set -a && source .env && set +a
nohup yarn start > /tmp/backstage.log 2>&1 &
disown
```

## Confirmar que levantó bien

El frontend (webpack-dev-server) suele quedar listo antes que el backend termine de compilar. Para saber cuándo el backend ya responde:

```bash
until curl -s -o /dev/null -w "%{http_code}" http://localhost:7007/api/catalog/entities | grep -q 200; do sleep 2; done
echo "backend listo"
```

Si corriste en background con `nohup`, podés revisar el progreso mientras tanto:

```bash
tail -f /tmp/backstage.log
```

## Reiniciar (necesario después de tocar `app-config.yaml` o `app-config.local.yaml`)

El backend **no** recarga la configuración en caliente — un cambio en esos archivos no tiene efecto hasta reiniciar el proceso completo.

```bash
pkill -f "backstage-cli repo start"
pkill -f "node /home/ramisistemas/.local/bin/yarn start"
sleep 2
ss -ltnp | grep -E ':3001|:7007'   # confirmar que los puertos quedaron libres; si no, matar el PID que aparezca
```

Y volver a arrancar con el mismo bloque de la sección "Arrancar".

## Login con GitHub
Una vez que frontend y backend están arriba, entrar a http://localhost:3001 y loguearse con GitHub. Las credenciales de la OAuth App (Client ID/Secret, callback) están en `.env` — no se documentan los valores acá por seguridad.

## Problema conocido: el catálogo muestra muy pocos templates/entidades
Si al entrar a Backstage el catálogo aparece casi vacío (por ejemplo, solo 1 template en vez de los ~36 esperados), revisar `backstage/app-config.local.yaml`: un bloque `catalog.locations` ahí **reemplaza por completo** (no fusiona) la lista de `app-config.yaml`, ocultando todo lo demás. La solución es no declarar `catalog.locations` en el archivo local, o replicar ahí toda la lista completa.

## Verificación rápida del catálogo
```bash
# Cuántos templates hay registrados
curl -s "http://localhost:7007/api/catalog/entities?filter=kind=template" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"

# Cuántos componentes hay registrados
curl -s "http://localhost:7007/api/catalog/entities?filter=kind=component" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
```
