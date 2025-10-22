# ⚡ GUIA RÁPIDO - 5 MINUTOS

Sistema Unificado para geração de guias e mapas mentais.

---

## 🎯 INSTALAÇÃO RÁPIDA

### 1. Criar Estrutura

```bash
# Execute o script de setup
python setup_structure.py

# Entre no diretório
cd sistema-unificado
```

### 2. Ambiente Virtual

```bash
# Crie o ambiente
python -m venv venv

# Ative (Linux/Mac)
source venv/bin/activate

# Ative (Windows)
venv\Scripts\activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar API Keys

```bash
# Copie o exemplo
cp .env.example .env

# Edite e adicione suas keys
nano .env  # ou notepad .env no Windows
```

Adicione pelo menos uma API key:
```env
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 🚀 PRIMEIRO USO

### 1. Validar Instalação

```bash
python scripts/validate_setup.py
```

Se tudo OK, você verá:
```
✅ Passou: 7/7
🎉 SISTEMA PRONTO PARA USO!
```

### 2. Iniciar Servidor

```bash
python run.py
```

Você verá:
```
🚀 SISTEMA UNIFICADO - GUIAS E MAPAS MENTAIS
🌐 URL: http://0.0.0.0:8000
💡 Interface Web: http://localhost:8000
```

### 3. Acessar Interface

Abra no navegador:
```
http://localhost:8000
```

---

## 📝 CRIAR SEU PRIMEIRO PROJETO

### 1. Copie o Exemplo

```bash
cp config/projetos/exemplo.yaml config/projetos/meu_projeto.yaml
```

### 2. Edite o Arquivo

```yaml
projeto:
  nome: "Meu Primeiro Projeto"
  area_conhecimento: "Direito Constitucional"
  radical_arquivo: "dConst"

topicos:
  - "Direitos Fundamentais"
  - "Organização do Estado"

modelos_guias:
  gerador:
    provedor: "anthropic"  # ou openai, gemini, deepseek
    modelo: "claude-sonnet-4-5-20250929"
  revisor:
    provedor: "anthropic"
    modelo: "claude-opus-4-20250514"

modelos_mapas:
  divisor:
    provedor: "anthropic"
    modelo: "claude-sonnet-4-5-20250929"
  gerador:
    provedor: "anthropic"
    modelo: "claude-sonnet-4-5-20250929"
  revisor:
    provedor: "anthropic"
    modelo: "claude-opus-4-20250514"
```

### 3. Processar na Interface

1. Acesse http://localhost:8000
2. Clique em **"Pipeline Completo"**
3. Faça upload do `meu_projeto.yaml`
4. Escolha modo **"Paralelo"** (mais rápido)
5. Clique em **"Iniciar Pipeline Completo"**

### 4. Acompanhe o Progresso

A interface mostrará:
- ✅ Progresso em tempo real
- 📊 Logs coloridos
- 📁 Arquivos gerados

### 5. Resultados

Após conclusão, encontre seus arquivos:

```
output/
├── guias/
│   ├── dConst01_DirFun.html
│   └── dConst02_OrgEst.html
└── mapas/
    ├── dConst01_DirFun_parte01.mmd
    ├── dConst01_DirFun_parte02.mmd
    ├── dConst02_OrgEst_parte01.mmd
    └── dConst02_OrgEst_parte02.mmd
```

---

## 🎛️ MODOS DE USO

### Modo 1: Pipeline Completo (Recomendado)

Gera **guias E mapas** automaticamente:

```
YAML → Guias HTML → Mapas .mmd
```

**Use quando:** Quer tudo de uma vez (mais prático)

---

### Modo 2: Só Guias

Gera **apenas guias HTML**:

```
YAML → Guias HTML
```

**Use quando:** 
- Quer revisar os HTMLs antes de gerar mapas
- Só precisa dos guias

---

### Modo 3: Só Mapas

Gera **mapas de HTMLs existentes**:

```
HTMLs prontos → Mapas .mmd
```

**Use quando:** 
- Já tem guias prontos
- Quer regenerar apenas os mapas

---

## ⚙️ ESCOLHER MODO DE PROCESSAMENTO

### Sequencial (Padrão)

```
Parte 1 → Parte 2 → Parte 3 → ...
```

✅ Mais estável
✅ Menor custo de API
⏱️ Mais lento

**Use quando:** Tem poucos tópicos ou quer economizar

---

### Paralelo (Recomendado)

```
Parte 1 ┐
Parte 2 ├→ Processa simultaneamente
Parte 3 ┘
```

✅ 2-5x mais rápido
✅ Melhor para muitos tópicos
💰 Mais chamadas de API

**Use quando:** Tem muitos tópicos e quer velocidade

---

## 🔧 CONFIGURAÇÃO DOS PROVIDERS

### Anthropic (Claude) - RECOMENDADO

```yaml
provedor: "anthropic"
modelo: "claude-sonnet-4-5-20250929"  # Rápido e bom
# ou
modelo: "claude-opus-4-20250514"      # Melhor qualidade
```

### OpenAI (GPT)

```yaml
provedor: "openai"
modelo: "gpt-4.1"                     # Melhor
# ou
modelo: "gpt-3.5-turbo"               # Mais barato
```

### Google (Gemini)

```yaml
provedor: "gemini"
modelo: "gemini-2.5-pro"              # Melhor
# ou
modelo: "gemini-2.0-flash"            # Mais rápido
```

### DeepSeek

```yaml
provedor: "deepseek"
modelo: "deepseek-reasoner"           # Raciocínio
# ou
modelo: "deepseek-chat"               # Geral
```

---

## 💡 DICAS RÁPIDAS

### 1. Economizar API Calls

- Use modo **sequencial**
- Use modelos **menores** (ex: gpt-3.5-turbo)
- Reduza `max_tentativas_revisao` para 2

### 2. Velocidade Máxima

- Use modo **paralelo**
- Configure `max_paralelo: 5`
- Use `mapas_max_workers_per_file: 5`

### 3. Qualidade Máxima

- Use **Claude Opus** como revisor
- Configure `max_tentativas_revisao: 3`
- Reduza `temperatura` para 0.3

### 4. Mix de Providers

```yaml
modelos_guias:
  gerador:
    provedor: "openai"      # Rápido para gerar
  revisor:
    provedor: "anthropic"   # Preciso para revisar
```

---

## 🐛 RESOLUÇÃO RÁPIDA DE PROBLEMAS

### Erro: "Provider não configurado"

**Solução:** Adicione API key no `.env`

```bash
nano .env
# Adicione: ANTHROPIC_API_KEY=sk-ant-...
```

---

### Erro: "Rate limit"

**Solução:** Aguarde 2 minutos ou use outro provider

---

### HTMLs não aparecem em output/guias/

**Solução:** Verifique logs:

```bash
tail -f logs/app_*.log
```

---

### Interface não carrega

**Solução:** Verifique se servidor está rodando:

```bash
curl http://localhost:8000/health
```

---

## 📚 PRÓXIMOS PASSOS

Após dominar o básico:

1. 📖 Leia `docs/API.md` para uso via API
2. 📋 Consulte `ROTEIRO_IMPLEMENTACAO.md` para detalhes técnicos
3. 🎯 Crie projetos customizados com muitos tópicos
4. 🚀 Experimente diferentes combinações de providers

---

## 🆘 PRECISA DE AJUDA?

```bash
# Valide instalação
python scripts/validate_setup.py

# Veja logs
ls -la logs/

# Health check
curl http://localhost:8000/health
```

**Documentação completa:** `docs/`

---

## ✅ CHECKLIST DE SUCESSO

- [ ] ✅ Script de setup executado
- [ ] ✅ Ambiente virtual criado e ativado
- [ ] ✅ Dependências instaladas
- [ ] ✅ Arquivo .env configurado com API key
- [ ] ✅ Validação OK (`validate_setup.py`)
- [ ] ✅ Servidor iniciado (`run.py`)
- [ ] ✅ Interface acessível no navegador
- [ ] ✅ Primeiro projeto processado com sucesso
- [ ] ✅ Arquivos gerados em `output/`

**Parabéns! 🎉 Sistema configurado e funcionando!**