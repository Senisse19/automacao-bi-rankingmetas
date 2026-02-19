
-- Tabela de Serviços (Produtos)
CREATE TABLE IF NOT EXISTS public.nexus_servicos (
    codigo BIGINT PRIMARY KEY,
    nome TEXT,
    sigla TEXT,
    modelo INT,
    sub_produto INT,
    ativo INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de Contratos Recorrentes (Dados Financeiros/Cadastrais)
CREATE TABLE IF NOT EXISTS public.nexus_contratos_recorrentes (
    codigo BIGINT PRIMARY KEY,
    tipo_contrato INT,
    participante BIGINT, -- Link com Job.codigo_cliente
    data_cadastro TIMESTAMPTZ,
    ativo_int INT, -- 1=Ativo? Validar com inspeção
    data_assinatura TIMESTAMPTZ,
    fim_contrato TIMESTAMPTZ,
    regime_tributacao INT,
    valor_a_vista NUMERIC(15,2),
    mensalidade NUMERIC(15,2),
    status TEXT, -- Campo derivado ou vindo da API
    observacao TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance no Join
CREATE INDEX IF NOT EXISTS idx_nexus_contratos_participante ON public.nexus_contratos_recorrentes(participante);
CREATE INDEX IF NOT EXISTS idx_nexus_contratos_ativo ON public.nexus_contratos_recorrentes(ativo_int);
