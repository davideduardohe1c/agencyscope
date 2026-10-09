# AgencyScope V3 — Benchmark competitivo con mirada gerencial

AgencyScope V3 retoma el proyecto de benchmarking de agencias y añade una capa de **inteligencia de negocio**.

La lógica sigue siendo competitiva: se analizan dominios públicos de agencias. Sin embargo, V3 ya no se queda únicamente en marketing táctico; intenta entender el **sistema comercial y de negocio visible** detrás de cada competidor.

## Novedades de V3

### 1. Inteligencia de negocio
Para cada agencia se analiza:
- modelo comercial visible
  - retainer / mensualidad
  - proyecto
  - performance
  - paquetes
  - suscripción / recurrencia
  - cotización personalizada
- sales motion
- mix de adquisición visible
- señales de crecimiento
- proxy de madurez pública
- transparencia comercial
- alertas gerenciales

### 2. Lente financiera
La clase reforzó la importancia de:
- ingresos
- costos
- EBITDA
- deuda
- ROE

Pero estos datos casi nunca son públicos para una agencia privada.

AgencyScope **no inventa** esos indicadores. La nueva sección diferencia:
- observable
- inferible
- no público

Se usan señales como pricing, recurrencia, prueba, casos, funnel y adquisición para complementar el benchmark sin presentar una inferencia como un estado financiero real.

### 3. Dashboard ejecutivo
Se agregaron:
- líderes por posicionamiento
- líder por prueba comercial
- líder por madurez pública
- líder por transparencia comercial
- empresa con mix de adquisición más amplio
- hallazgos estratégicos automáticos

### 4. Nuevas gráficas
- Posicionamiento vs prueba
- Madurez pública vs transparencia comercial
- Mix visible de adquisición
- Comparación de puntajes

## Cómo ejecutarlo en Mac

```bash
cd ~/Downloads/AgencyScope_V3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PORT=5055 python app.py
```

Luego abre:

`http://127.0.0.1:5055`

También puedes usar `run_mac.command`.

## Regla metodológica

AgencyScope sirve para formular hipótesis de negocio desde evidencia pública.

No afirma:
- ingresos reales de una agencia privada,
- costos,
- EBITDA,
- deuda,
- ROE,
- inversión publicitaria exacta,
- targeting privado.

Si esos datos no son públicos, se muestran como **no observables**.

Esto hace que el benchmark sea más útil para toma de decisiones y, al mismo tiempo, metodológicamente defendible.
