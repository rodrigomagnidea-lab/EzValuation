# EzValuation - Investment Thesis Generator

Aplicação Streamlit para análise estruturada de Fundos Imobiliários (FIIs) com metodologias personalizáveis.

## 🚀 Funcionalidades

- **Autenticação**: Login via Supabase Auth
- **Análise de FIIs**: Wizard interativo para avaliação estruturada
- **Valuation**: Calculadoras financeiras (Gordon, IPCA+, FCFE)
- **Metodologias**: Sistema configurável de pilares, critérios e faixas
- **Exportação**: Geração de relatórios em PDF
- **Admin Panel**: CRUD completo para gestão de metodologias

## 📋 Pré-requisitos

- Python 3.8+
- Conta no Supabase
- Banco de dados configurado (ver SQL fornecido)

## ⚙️ Instalação

1. Clone o repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure o Supabase:

Edite o arquivo `.streamlit/secrets.toml`:

```toml
[supabase]
url = "https://seu-projeto.supabase.co"
key = "sua-chave-anon"
```

4. Execute a aplicação:

```bash
streamlit run app.py
```

## 🏗️ Estrutura do Projeto

```
App-ezvaluation/
├── app.py                      # Aplicação principal
├── requirements.txt            # Dependências
├── .streamlit/
│   └── secrets.toml           # Credenciais Supabase
├── utils/
│   ├── auth.py               # Autenticação
│   ├── db.py                 # Operações de banco
│   └── valuation.py          # Modelos financeiros
└── pages/
    ├── admin_methodology.py  # Painel admin
    └── analysis_wizard.py    # Wizard de análise
```

## 👤 Roles de Usuário

### Usuário Regular
- Criar análises de FIIs
- Visualizar análises salvas
- Usar calculadoras de valuation
- Exportar relatórios PDF

### Administrador
- Todas as funcionalidades de usuário
- Criar/editar metodologias
- Gerenciar pilares, critérios e faixas
- Ativar/desativar versões de metodologia

**Para configurar um usuário como admin:**

No Supabase, adicione à tabela `auth.users`:

```sql
UPDATE auth.users
SET raw_user_meta_data = '{"role": "admin"}'::jsonb
WHERE email = 'admin@exemplo.com';
```

## 📊 Fluxo de Uso

### Para Administradores:

1. Acesse "Admin: Metodologias"
2. Crie uma nova metodologia ou edite existente
3. Adicione pilares (ex: "Gestão e Governança")
4. Para cada pilar, adicione critérios (ex: "Histórico da Gestora")
5. Para cada critério, defina faixas de pontuação
6. Ative a metodologia desejada

### Para Usuários:

1. Acesse "Nova Análise"
2. Digite o ticker do FII (ex: HGLG11)
3. Selecione o segmento
4. Preencha os critérios apresentados
5. Visualize o score automático
6. Faça overrides manuais se necessário
7. Salve a análise
8. Exporte o PDF

## 🔧 Tecnologias

- **Frontend**: Streamlit
- **Backend**: Supabase (PostgreSQL)
- **Dados de Mercado**: yfinance
- **Visualização**: Plotly
- **Exportação**: FPDF2

## 📝 Licença

Este projeto é proprietário.

## 🤝 Suporte

Para dúvidas ou problemas, entre em contato com o administrador do sistema.
