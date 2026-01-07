# Guia de Configuração e Regras de Negócio

## 1. Conexão com Banco de Dados (Supabase)
O projeto utiliza o arquivo .streamlit/secrets.toml.
Tabelas: indices, methodologies, pillars, criteria, ranges, analyses.

## 2. Lógica das Metodologias (Core Business)
Estrutura hierárquica:
1. Metodologia (Raiz) - Taxa Livre de Risco, Prêmio de Risco.
2. Pilares (Peso) - Ex: Gestão, Qualidade.
3. Critérios (Input) - Ex: Vacância, P/VP.
4. Faixas (Score) - Regras de pontuação (0, 3, 5).

## 3. Regras de Segurança e UX (Admin)
- Trava de Exclusão: Obrigatório uso de Modal (st.dialog).
- Validação: Usuário deve digitar a palavra 'DELETAR' para confirmar.

## 4. Setup de Usuário Admin
Rodar no SQL Editor do Supabase para promover usuário:

UPDATE auth.users
SET raw_user_meta_data = jsonb_set(
  COALESCE(raw_user_meta_data, '{}'::jsonb),
  '{role}',
  '"admin"'
)
WHERE email = 'seu@email.com';
