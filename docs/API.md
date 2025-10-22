# 📡 API - SISTEMA UNIFICADO

Documentação completa dos endpoints da API.

---

## BASE URL

```
http://localhost:8000
```

---

## AUTENTICAÇÃO

Não há autenticação na versão atual (ambiente local).

---

## ENDPOINTS

### 1. 🏠 ROOT

#### GET `/`

Retorna a interface web.

**Response:** HTML da interface

---

### 2. 🚀 PIPELINE COMPLETO

#### POST `/api/process-full`

Executa pipeline completo: Guias → Mapas

**Request:**
```
Content-Type: multipart/form-data

- config_file: arquivo YAML de configuração
- modo: "sequencial" | "paralelo" (opcional, padrão: "sequencial")
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:8000/api/process-full \
  -F "config_file=@config/projetos/exemplo.yaml" \
  -F "modo=paralelo"
```

**Response:**
```json
{
  "status": "completed",
  "pipeline": "full",
  "guias": {
    "total": 10,
    "arquivos": [
      "dConst01_DirGarFun.html",
      "dConst02_OrgEst.html"
    ],
    "estatisticas": {
      "total": 10,
      "concluidos": 10,
      "erros": 0,
      "tokens_totais": {
        "input": 50000,
        "output": 30000
      },
      "tempo_total_ms": 300000
    }
  },
  "mapas": {
    "total": 25,
    "resultados": [
      {
        "html_file": "dConst01_DirGarFun.html",
        "status": "concluido",
        "partes_processadas": [
          {
            "parte_numero": 1,
            "parte_titulo": "Conceito e Características",
            "mapa_gerado": "mindmap\n  {{**Direitos Fundamentais**}}...",
            "aprovado": true,
            "nota_geral": 8.5
          }
        ]
      }
    ]
  }
}
```

---

### 3. 📚 APENAS GUIAS

#### POST `/api/process-guias-only`

Gera apenas os guias HTML (sem mapas).

**Request:**
```
Content-Type: multipart/form-data

- config_file: arquivo YAML de configuração
```

**Exemplo:**
```bash
curl -X POST http://localhost:8000/api/process-guias-only \
  -F "config_file=@config/projetos/exemplo.yaml"
```

**Response:**
```json
{
  "status": "completed",
  "pipeline": "guias-only",
  "resultado": {
    "status_geral": "concluido",
    "arquivos_gerados": [
      "dConst01_DirGarFun.html",
      "dConst02_OrgEst.html"
    ],
    "estatisticas": {
      "total": 10,
      "concluidos": 10,
      "erros": 0
    }
  }
}
```

---

### 4. 🗺️ APENAS MAPAS

#### POST `/api/process-mapas-only`

Gera mapas .mmd a partir de HTMLs existentes.

**Request:**
```
Content-Type: multipart/form-data

- html_files: lista de nomes de arquivos HTML
- config_file: arquivo YAML com configuração dos modelos
```

**Exemplo:**
```bash
curl -X POST http://localhost:8000/api/process-mapas-only \
  -F "html_files=dConst01_DirGarFun.html" \
  -F "html_files=dConst02_OrgEst.html" \
  -F "config_file=@config/projetos/exemplo.yaml"
```

**Response:**
```json
{
  "status": "completed",
  "pipeline": "mapas-only",
  "resultados": [
    {
      "html_file": "dConst01_DirGarFun.html",
      "status": "concluido",
      "partes_processadas": [...]
    }
  ]
}
```

---

### 5. ❤️ HEALTH CHECK

#### GET `/health`

Verifica saúde do sistema.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "providers": ["anthropic", "openai"],
  "features": {
    "guias": true,
    "mapas": true,
    "pipeline_completo": true
  }
}
```

---

## 📡 WEBSOCKET

### WS `/ws`

Conexão WebSocket para progresso em tempo real.

**Mensagens Recebidas:**

#### 1. Conexão
```json
{
  "type": "connection",
  "status": "connected",
  "timestamp": "2025-01-15T14:30:00"
}
```

#### 2. Progresso
```json
{
  "type": "progress",
  "stage": "guias|mapas|completo",
  "pipeline": "full|guias-only|mapas-only",
  "message": "Processando...",
  "percentage": 45,
  "timestamp": "2025-01-15T14:30:15"
}
```

#### 3. Log
```json
{
  "type": "log",
  "level": "info|success|warning|error",
  "message": "Guia gerado com sucesso",
  "timestamp": "2025-01-15T14:30:20"
}
```

#### 4. Conclusão
```json
{
  "type": "completion",
  "success": true,
  "pipeline": "full",
  "guias": {
    "total": 10,
    "arquivos": [...]
  },
  "mapas": {
    "total": 25
  },
  "timestamp": "2025-01-15T14:35:00"
}
```

**Exemplo JavaScript:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => console.log('Conectado');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'progress') {
    console.log(`Progresso: ${data.percentage}%`);
  }
  
  if (data.type === 'log') {
    console.log(`[${data.level}] ${data.message}`);
  }
  
  if (data.type === 'completion') {
    console.log('Processamento concluído!');
  }
};
```

---

## 🔄 WORKFLOW TÍPICO

### Pipeline Completo

1. Cliente envia YAML via `/api/process-full`
2. Cliente conecta ao WebSocket `/ws`
3. Sistema processa:
   - Parse do YAML
   - Geração de guias (envia progresso via WS)
   - Geração de mapas (envia progresso via WS)
4. Sistema retorna resultado final
5. Cliente desconecta WebSocket

### Fluxo Separado

**Etapa 1 - Guias:**
```bash
curl -X POST http://localhost:8000/api/process-guias-only \
  -F "config_file=@meu_projeto.yaml"
```

**Etapa 2 - Mapas (após guias prontos):**
```bash
curl -X POST http://localhost:8000/api/process-mapas-only \
  -F "html_files=dConst01.html" \
  -F "html_files=dConst02.html" \
  -F "config_file=@meu_projeto.yaml"
```

---

## 📊 CÓDIGOS DE STATUS

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 400 | Requisição inválida (YAML inválido, providers não configurados) |
| 500 | Erro interno (falha na geração, timeout LLM, etc) |

---

## ⚠️ ERROS COMUNS

### 1. Provider não configurado
```json
{
  "detail": "Provider 'anthropic' não está configurado. Adicione API key no .env"
}
```

**Solução:** Configure a API key no arquivo `.env`

### 2. YAML inválido
```json
{
  "detail": "Chave obrigatória ausente: modelos_guias"
}
```

**Solução:** Verifique estrutura do YAML contra `exemplo.yaml`

### 3. Rate Limit
```json
{
  "detail": "Rate limit atingido para anthropic"
}
```

**Solução:** Aguarde alguns minutos ou use outro provider

### 4. Timeout
```json
{
  "detail": "Timeout na operação: geração de guia"
}
```

**Solução:** Aumente `LLM_TIMEOUT` no `.env` ou reduza `max_tokens`

---

## 🔐 SEGURANÇA

**⚠️ IMPORTANTE:**

- Este sistema é para uso **LOCAL** apenas
- Não exponha à internet sem autenticação
- API keys ficam no servidor (`.env`)
- Nunca commite `.env` no git

---

## 📝 EXEMPLOS PRÁTICOS

### Python
```python
import requests

# Pipeline completo
with open('config/projetos/exemplo.yaml', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/process-full',
        files={'config_file': f},
        data={'modo': 'paralelo'}
    )

result = response.json()
print(f"Guias: {result['guias']['total']}")
print(f"Mapas: {result['mapas']['total']}")
```

### JavaScript/Node.js
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('config_file', fs.createReadStream('exemplo.yaml'));
form.append('modo', 'paralelo');

axios.post('http://localhost:8000/api/process-full', form, {
  headers: form.getHeaders()
})
.then(response => {
  console.log('Guias:', response.data.guias.total);
  console.log('Mapas:', response.data.mapas.total);
})
.catch(error => {
  console.error('Erro:', error.message);
});
```

---

## 🔗 LINKS ÚTEIS

- Documentação Interativa: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

---

## 📞 SUPORTE

Para dúvidas ou problemas:
1. Verifique logs em `logs/`
2. Consulte `ROTEIRO_IMPLEMENTACAO.md`
3. Execute `python scripts/validate_setup.py`