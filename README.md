# EzValuation - Investment Thesis Generator

Aplicação Streamlit desenvolvida em arquitetura **SPA (Single Page Application)** para análise estruturada de Fundos Imobiliários (FIIs).

## 🚀 Funcionalidades Atuais
- **Autenticação Segura**: Login via Supabase Auth.
- **Análise de FIIs (Wizard)**: Fluxo passo-a-passo.
- **Valuation Engine**: Gordon, IPCA+, WACC, FCFE.
- **Gestão de Metodologias (Admin)**: Pilares, Critérios e Faixas.
- **Gestão de Índices (Admin)**: CRUD de indicadores.
- **Exportação**: Relatórios em PDF.

## 🏗️ Arquitetura do Projeto (SPA)
Este projeto usa roteamento centralizado no app.py.

App-ezvaluation/
├── app.py                      # ROTEADOR PRINCIPAL
├── utils/
│   ├── auth.py                 # Autenticação
│   ├── db.py                   # Supabase
│   └── sidebar.py              # Menu Lateral
└── interfaces/                 # VIEWS (Telas)
    ├── admin_methodology.py
    ├── admin_market_data.py
    └── analysis_wizard.py

## 👤 Perfis de Acesso
1. **Usuário Comum**: Nova Análise, Valuation.
2. **Administrador**: Gestão de Metodologias e Índices.

## 🔧 Stack
- Frontend: Streamlit (Python puro)
- Backend: Supabase (PostgreSQL)
- Libs: yfinance, plotly, fpdf2

## ⚠️ Notas de Desenvolvimento
- Navegação controlada pelo app.py e utils/sidebar.py.
- Pasta 'pages/' do Streamlit foi DESATIVADA.
- Operações de exclusão exigem digitar 'DELETAR'.
