# EzValuation - Guia de Configuração Inicial

## 1. Configurar Supabase

### 1.1. Obter Credenciais

1. Acesse seu projeto no [Supabase](https://supabase.com)
2. Vá em **Settings** → **API**
3. Copie:
   - **Project URL** (ex: `https://abcdefgh.supabase.co`)
   - **anon public** key

### 1.2. Configurar secrets.toml

Edite o arquivo `.streamlit/secrets.toml`:

```toml
[supabase]
url = "https://seu-projeto-id.supabase.co"
key = "sua-chave-anon-aqui"
```

### 1.3. Executar SQL de Criação do Banco

Execute o script SQL fornecido anteriormente no SQL Editor do Supabase.

## 2. Criar Usuário Admin

No SQL Editor do Supabase, após criar seu primeiro usuário via Auth:

```sql
-- Listar usuários existentes
SELECT id, email, raw_user_meta_data FROM auth.users;

-- Tornar um usuário admin
UPDATE auth.users
SET raw_user_meta_data = jsonb_set(
  COALESCE(raw_user_meta_data, '{}'::jsonb),
  '{role}',
  '"admin"'
)
WHERE email = 'seu@email.com';
```

## 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

## 4. Executar a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

## 5. Primeiro Uso

### Como Admin:

1. Faça login
2. Acesse "Admin: Metodologias"
3. Crie sua primeira metodologia:
   - Versão: "FII Tijolo v1.0"
   - IPCA: 4.5%
   - NTN-B Real: 6.0%
4. Adicione pilares (ex: "Gestão e Governança", "Localização", "Qualidade dos Ativos")
5. Para cada pilar, adicione critérios
6. Para cada critério, defina faixas de pontuação
7. Ative a metodologia

### Como Usuário:

1. Faça login
2. Acesse "Nova Análise"
3. Digite um ticker (ex: HGLG11)
4. Preencha o formulário
5. Salve e exporte

## 6. Troubleshooting

### Erro de conexão com Supabase
- Verifique se as credenciais em `secrets.toml` estão corretas
- Confirme que o IP está autorizado no Supabase (se houver restrições)

### Erro de RLS (Row Level Security)
- Certifique-se de que as políticas RLS foram criadas
- Verifique se o usuário está autenticado corretamente

### Erro ao buscar dados de FII
- O ticker deve incluir `.SA` (ex: `HGLG11.SA`)
- Verifique conexão com internet
- O yfinance pode ter limitações de rate

## 7. Estrutura de Dados Recomendada

Exemplo de metodologia inicial:

**Pilar: Gestão e Governança (Peso: 2)**
- Critério: Histórico da Gestora (numeric, anos)
  - 0-5 anos: 0 pts (red)
  - 5-10 anos: 3 pts (yellow)
  - 10+ anos: 5 pts (green)

**Pilar: Localização (Peso: 1.5)**
- Critério: Região Metropolitana (boolean)
  - Não: 0 pts (red)
  - Sim: 5 pts (green)

**Pilar: Qualidade dos Ativos (Peso: 2)**
- Critério: Vacância Física (percent, %)
  - 0-5%: 5 pts (green)
  - 5-15%: 3 pts (yellow)
  - 15%+: 0 pts (red)
