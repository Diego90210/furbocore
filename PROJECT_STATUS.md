# Furbocore — Estado del Proyecto

## Infraestructura

| Componente | Estado | URL |
|------------|--------|-----|
| **Supabase** | ✅ Activo | `kswtdayhvzzhrbdwzgqb.supabase.co` |
| **Vercel** | ✅ Deployed | https://furbocore.vercel.app |
| **GitHub Actions** | ✅ 2 workflows activos | `transfer-value-pipeline` (monthly), `match-pipeline` (weekly) |

## Tablas — Estado de datos

| Tabla | Registros | Fuente | Problema |
|-------|-----------|--------|----------|
| `players` | 2,259 | Transfermarkt CSV (R2) | — |
| `transfer_values` | 2,259 | Transfermarkt CSV (R2) | — |
| `player_stats` | 0 | FBref (soccerdata) | **FBref bloquea requests (403)** |
| `matches` | 0 | football-data.co.uk (soccerdata) | **Sitio retorna 503** |
| `match_predictions` | 0 | Generado por ML | Depende de `matches` |
| `player_clusters` | 0 | Generado por ML | Depende de `player_stats` |

## Módulos — Estado de funcionalidad

### Transfer Values (`/transfers`)
- ✅ 2,259 jugadores PL con nombre, equipo, posición
- ✅ 2,259 predicciones de valor (RandomForest, solo posición como feature)
- ✅ 969 valores reales de Transfermarkt + gap analysis
- ⚠️ Modelo simplificado: solo usa position one-hot (sin stats por partido)
- ⚠️ Snapshot histórico de Transfermarkt: jugadores de temporadas pasadas (no incluye Haaland, Bellingham, etc.)

### Match Predictions (`/matches`)
- ❌ Sin datos — football-data.co.uk retorna 503
- ❌ No hay modelo entrenado
- ❌ Página funcional pero vacía

### Scouting (`/scouting`)
- ❌ Sin datos — depende de `player_stats` (FBref)
- ❌ No hay clusters entrenados
- ❌ RPC `similar_players` configurada pero sin datos

## Problema raíz: fuentes de datos bloqueadas

### FBref (via soccerdata)
- **Error**: `HTTPError: 403 Forbidden`
- **Afecta**: `player_stats` → `player_clusters` → scouting
- **Causa**: FBref bloquea scraping automatizado
- **Funciona en GitHub Actions**: Posiblemente no (mismo bloqueo)

### football-data.co.uk (via soccerdata)
- **Error**: `HTTPError: 503 Service Unavailable`
- **Afecta**: `matches` → `match_predictions` → match outcomes
- **Causa**: Servicio temporalmente caído o bloqueando requests
- **Funciona en GitHub Actions**: Posiblemente no

### Transfermarkt (vía R2)
- **Estado**: ✅ Funcional
- **Datos**: CSV cacheados en `data/raw/` (50k jugadores, 656k valuaciones)
- **Limitación**: Snapshot histórico, sin datos de rendimiento por partido

## Pipeline ML ejecutado

| Pipeline | Estado | Algoritmo | Features |
|----------|--------|-----------|----------|
| Transfer Value | ✅ Entrenado | RandomForest (200 trees, depth=10) | Position one-hot (4 features) |
| Match Outcome | ❌ Sin datos | XGBClassifier | Form (no leakage) + Elo |
| Scouting | ❌ Sin datos | KMeans (k=3..8 per group) | Per-90 stats, scaled |

### Modelo de Transfer Value — Limitaciones
- Solo 4 features: `pos_DF`, `pos_FW`, `pos_GK`, `pos_MF`
- MAE alto porque no usa edad, minutos, goles, asistencias
- Promedio de gap predicho vs real: ~122% (sobreestima significativamente)
- Modelo funcional pero no preciso para análisis real

## Archivos clave

```
app/
  layout.tsx          # Nav + footer
  page.tsx            # Landing
  transfers/          # Search + player card + stats
  matches/            # Match cards con probabilidades
  scouting/           # Search + radar chart +相似 juadores

src/
  ingestion/
    fbref_players.py         # FBref → players + player_stats (BLOQUEADO)
    transfermarkt_values.py  # R2 → players + transfer_values (FUNCIONAL)
    matches_and_elo.py       # football-data.co.uk → matches (BLOQUEADO)
  features/
    transfer_value.py        # Per-90 stats + one-hot (necesita player_stats)
    match_outcome.py         # Form + elo (necesita matches)
    scouting.py              # Normalize + scale (necesita player_stats)
  models/
    transfer_value/
      run_pipeline.py        # All-in-one train+predict (FUNCIONA sin FBref)
      train.py               # Original (necesita player_stats)
      predict.py             # Original (necesita player_stats)
    match_outcome/
      train.py               # XGBClassifier
      predict.py             # Predict scheduled matches
    scouting/
      train.py               # KMeans per group
      predict.py             # Assign clusters + upsert vector

.github/workflows/
  transfer-value-pipeline.yml  # Monthly, continue-on-error
  match-pipeline.yml           # Weekly, continue-on-error
```

## Env vars configuradas

| Variable | GitHub Actions | Vercel | .env.local |
|----------|---------------|--------|------------|
| `SUPABASE_URL` | ✅ Secret | ✅ Env var | ✅ |
| `SUPABASE_SERVICE_KEY` | ✅ Secret | — | ✅ |
| `NEXT_PUBLIC_SUPABASE_URL` | — | ✅ Env var | ✅ |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | — | ✅ Env var | ✅ |

## Próximos pasos

1. **Poblar `player_stats`**: Buscar fuente alternativa a FBref o generar datos sintéticos desde Transfermarkt
2. **Poblar `matches`**: Re-intentar football-data.co.uk o encontrar fuente alternativa
3. **Entrenar modelos reales**: Con datos completos, re-entrenar transfer value con stats por 90 min
4. **Mejorar scouting**: Con player_stats, entrenar clusters y habilitar similaridad
5. **Producción**: Conectar dominio, monitoreo, actualización automática
