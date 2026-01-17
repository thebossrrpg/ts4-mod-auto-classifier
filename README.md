# TS4 Mod Auto-Classifier

Sistema completo de classificação automática de mods do The Sims 4 com busca inteligente no Notion e integração com LLM.

## 🎯 Funcionalidades

- **Busca Inteligente no Notion**: Encontra automaticamente páginas de mods no Notion usando:
  - URL do mod
  - URL da página do Notion
  - Combinação nome + criador
- **Classificação Automática**: Analisa o conteúdo do mod e atribui prioridade (1-5) usando LLM
- **Extração de Conteúdo**: Extrai texto e imagens das páginas de mods
- **Atualização Automática**: Atualiza propriedades no Notion (prioridade, pasta, notas)
- **Criação Automática**: Cria nova página no Notion se não encontrar o mod

## 📋 Requisitos

- Python 3.9+
- Conta Notion com API Key
- LLM API Key (OpenAI, Anthropic, etc.)
- Database do Notion configurada

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/thebossrrpg/ts4-mod-auto-classifier.git
cd ts4-mod-auto-classifier
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:
```
NOTION_API_KEY=seu_token_aqui
NOTION_DB_ID=id_da_database
LLM_API_KEY=sua_chave_api
```

## 💻 Uso

### Interface Streamlit

```bash
streamlit run streamlit_app.py
```

### Uso Programático

```python
from src.classifier import ModClassifier

classifier = ModClassifier()

# Por URL do mod
result = classifier.classify("https://modthesims.info/d/12345")

# Por URL da página do Notion
result = classifier.classify("https://notion.so/Mod-Name-abc123")

print(f"Prioridade: {result['priority']}")
print(f"Pasta: {result['folder']}")
```

## 📁 Estrutura do Projeto

```
ts4-mod-auto-classifier/
├── src/
│   ├── __init__.py
│   ├── classifier.py       # Classificador principal
│   ├── notion_handler.py   # Integração com Notion
│   ├── content_extractor.py # Extração de conteúdo
│   └── llm_client.py       # Cliente LLM
├── prompts/
│   └── classification_prompt.txt
├── config/
│   └── settings.py
├── streamlit_app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔍 Como Funciona

1. **Input**: Recebe URL do mod ou URL da página do Notion
2. **Busca**: Procura a página correspondente no Notion
3. **Extração**: Extrai conteúdo da página do mod (se necessário)
4. **Classificação**: Envia conteúdo para LLM com prompt de classificação
5. **Atualização**: Atualiza/cria página no Notion com:
   - Prioridade (1-5)
   - Pasta correspondente
   - Notas (para prioridades 3+)

## ⚙️ Configuração do Notion

Sua database deve ter as seguintes propriedades:

- **Nome** (Title): Nome do mod
- **Criador** (Text): Criador do mod
- **Link** (URL): Link do mod
- **Prioridade** (Number): 1-5
- **Pasta** (Select): 00-Must Have, 01-Core, etc.
- **Notes** (Text): Justificativa da classificação

## 📝 License

MIT License - veja LICENSE para detalhes


