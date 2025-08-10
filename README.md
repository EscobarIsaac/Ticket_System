# TicketSystem — Flask + MongoDB + Sistema Experto (Prolog)

Sistema de gestión de tickets con **Flask**, **MongoDB** y un **Asistente Virtual** (sistema experto en **SWI‑Prolog**).  
Incluye **roles**: *cliente*, *soporte* y *superadmin*. El asistente guía al cliente con pasos de diagnóstico; si no resuelve, **escala el ticket** a un técnico automáticamente. También incorpora **notificaciones** y un **chat flotante** tipo burbuja.

---

## 🚀 Características
- **Autenticación** por roles (cliente, soporte, superadmin).
- **Creación y gestión de tickets** (estado, prioridad, asignación, historial).
- **Notificaciones** con campanita y badge.
- **Sistema experto (Prolog)** integrado en el chat:
  - Sugerencias por categoría del problema.
  - Flujo guiado (3–4 pasos). Si no resuelve → **escala a soporte**.
  - Si el cliente responde “solucionado”, **cierra el ticket**.
- **Dashboards** por rol (cliente/soporte/admin).
- **Pruebas automatizadas** con **pytest**.

---

## 📦 Requisitos
- **Python 3.10+** (probado con 3.12)
- **SWI‑Prolog** instalado y en el PATH del sistema  
  - Windows: https://www.swi-prolog.org/download/stable
- **MongoDB** (usa tu cadena `MONGO_URI` o la de ejemplo incluida)

> 💡 El proyecto ya maneja correctamente rutas en Windows para cargar `sistema_experto/sistemaexperto.pl`.

---

## 🗂️ Estructura (resumen)
```
proyecto-aseguramiento/
├─ app.py
├─ sistema_experto/
│  └─ sistemaexperto.pl
├─ templates/
│  ├─ login.html
│  ├─ register.html
│  ├─ dashboard_cliente.html
│  ├─ dashboard_soporte.html
│  ├─ dashboard_admin.html
│  ├─ ticket_detail.html
│  └─ notifications.html
├─ static/
│  └─ css/style.css
└─ tests/
   ├─ conftest.py
   ├─ test_auth.py
   ├─ test_tickets.py
   └─ test_chat.py
```

---

## ⚙️ Instalación y ejecución

### 1) Clonar o descomprimir
```bash
# Clonar
git clone https://tu-repo.github.io/tickets-prolog.git
cd tickets-prolog

# O si descargaste .zip: descomprime y entra a la carpeta
```

### 2) Crear y activar entorno virtual
```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3) Instalar dependencias
```bash
pip install -r requirements.txt
```
Si no cuentas con `requirements.txt`, instala manualmente:
```bash
pip install Flask pymongo certifi python-dotenv pyswip pytest mongomock
```

### 4) Variables de entorno (opcional)
Crea un archivo `.env` en la raíz (opcional):
```
FLASK_SECRET=una_clave_segura
MONGO_URI=mongodb+srv://usuario:clave@cluster/tuDB?retryWrites=true&w=majority
```
> Si no defines `MONGO_URI`, la app usa una de ejemplo ya incluida en `app.py`.

### 5) Ejecutar la app
```bash
python app.py
```
Abre: http://127.0.0.1:5000

---

## 👤 Usuarios de prueba
- **Soporte:** usuario `isaac` — contraseña `isaac1`
- **Cliente:** usuario `katy` — contraseña `katy1` *(o regístrate desde /register)*
- **Admin:** usuario `isaac1` — contraseña `isaac1`

> Puedes crear más usuarios cliente desde **/register**. Los roles de soporte/admin se gestionan desde BD o desde el flujo de admin que crea técnicos.

---

## 🧪 Ejecutar pruebas
Asegúrate de tener el venv activo y dependencias instaladas:
```bash
pytest -q
```
Las pruebas incluyen:
- **Auth** (login/registro)
- **Tickets** (crear/asignar/resolver, historial)
- **Chat experto** (flujo de pasos, cierre, escalado)

> Las pruebas usan **mongomock** (BD en memoria) para no tocar tus datos reales.

---

## 🧩 Notas sobre SWI‑Prolog
- Debe estar instalado y accesible en el **PATH** del sistema.
- El proyecto usa:
  - `working_directory(_, PATH)` y `consult('sistema_experto/sistemaexperto.pl')`
  - Esto evita problemas de backslashes (`\`) en Windows.
- Si ves un error tipo *“Unknown character escape”* verifica que **NO** se estén pasando rutas con backslash a Prolog. La app ya usa rutas POSIX para consult.

---

## 🛠️ Comandos rápidos

```bash
# 1) Crear venv + activar
python -m venv venv
venv\Scripts\activate   # (Windows)
# source venv/bin/activate  # (Linux/Mac)

# 2) Instalar dependencias
pip install -r requirements.txt
# o bien:
pip install Flask pymongo certifi python-dotenv pyswip pytest mongomock

# 3) Ejecutar
python app.py

# 4) Probar
pytest -q
```

---

## 📄 Licencia
Proyecto académico. Úsalo libremente para aprendizaje y prácticas.
