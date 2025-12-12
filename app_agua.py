import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Hidratação Marketing", page_icon="💧", layout="wide")

# --- ARQUIVOS ---
FILE_USUARIOS = 'usuarios.csv'
FILE_ESTOQUE = 'estoque.csv'

# --- FUNÇÕES DE CARREGAMENTO E LIMPEZA ---
def carregar_usuarios():
    if not os.path.exists(FILE_USUARIOS):
        # Cria dataframe inicial limpo
        df = pd.DataFrame(columns=["Nome", "Divida", "Pago", "Copo_ML_Hoje"])
        return df
    
    df = pd.read_csv(FILE_USUARIOS)
    # Garante que os tipos estão certos para evitar erros de visualização
    # Preenche vazios (None) com 0 ou False
    df["Divida"] = df["Divida"].fillna(0.0).astype(float)
    df["Copo_ML_Hoje"] = df["Copo_ML_Hoje"].fillna(0).astype(int)
    df["Pago"] = df["Pago"].fillna(False).astype(bool)
    df["Nome"] = df["Nome"].astype(str)
    
    # Remove linhas onde o Nome é "nan" ou vazio (sujeira de edição)
    df = df[df["Nome"] != "nan"]
    df = df[df["Nome"] != ""]
    return df

def carregar_estoque():
    if not os.path.exists(FILE_ESTOQUE):
        data = {
            "Preco_Galao": [15.0],
            "Cheios": [2],
            "Vazios": [1],
            "Pedido_Feito": [False],
            "Data_Pedido": ["-"]
        }
        df = pd.DataFrame(data)
        df.to_csv(FILE_ESTOQUE, index=False)
        return df
    return pd.read_csv(FILE_ESTOQUE)

def salvar_dados(df, filename):
    df.to_csv(filename, index=False)

# --- INÍCIO DO APP ---
st.title("💧 Cota da Água - Marketing")

# Carrega dados iniciais
df_users = carregar_usuarios()
df_estoque = carregar_estoque()

# --- SIDEBAR: ESTOQUE (Correção do reset de valor) ---
st.sidebar.header("📦 Controle de Estoque")

# Usamos o session_state ou o valor direto do DF para persistir visualmente
preco_atual = float(df_estoque.iloc[0]['Preco_Galao'])
cheios_atual = int(df_estoque.iloc[0]['Cheios'])
vazios_atual = int(df_estoque.iloc[0]['Vazios'])
pedido_atual = bool(df_estoque.iloc[0]['Pedido_Feito'])

# Inputs do estoque
novo_preco = st.sidebar.number_input("Preço Galão (R$)", value=preco_atual, step=1.0)
cheios = st.sidebar.number_input("Galões Cheios", value=cheios_atual, step=1)
vazios = st.sidebar.number_input("Galões Vazios", value=vazios_atual, step=1)

st.sidebar.markdown("---")
ja_pediu = st.sidebar.checkbox("Pedido realizado?", value=pedido_atual)

# Lógica de atualização do estoque
if st.sidebar.button("💾 Atualizar Estoque"):
    # Verifica se o status do pedido mudou de False para True agora
    data_nova = df_estoque.iloc[0]['Data_Pedido']
    if ja_pediu and not pedido_atual:
        data_nova = datetime.now().strftime("%d/%m %H:%M")
    elif not ja_pediu:
        data_nova = "-"

    # Atualiza o DataFrame
    df_estoque.loc[0, 'Preco_Galao'] = novo_preco
    df_estoque.loc[0, 'Cheios'] = cheios
    df_estoque.loc[0, 'Vazios'] = vazios
    df_estoque.loc[0, 'Pedido_Feito'] = ja_pediu
    df_estoque.loc[0, 'Data_Pedido'] = data_nova
    
    salvar_dados(df_estoque, FILE_ESTOQUE)
    st.sidebar.success("Estoque salvo!")
    st.rerun() # Recarrega a página para fixar o valor

st.sidebar.info(f"Último pedido: {df_estoque.iloc[0]['Data_Pedido']}")

# --- ABAS PRINCIPAIS ---
tab1, tab2 = st.tabs(["💰 Lista & Pagamentos", "🏆 Gamificação (Ao Vivo)"])

# === ABA 1: TABELA FINANCEIRA ===
with tab1:
    col_a, col_b = st.columns([3, 1])
    
    with col_a:
        st.subheader("Gerenciar Pessoas e Dívidas")
        st.caption("Edite os nomes, valores ou marque como pago diretamente na tabela abaixo.")
        
        # O data_editor permite adicionar linhas. 
        # Quando o usuário adiciona, os campos vêm como None/NaN, precisamos tratar isso.
        df_editado = st.data_editor(
            df_users,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Nome": st.column_config.TextColumn("Nome", required=True),
                "Divida": st.column_config.NumberColumn("Dívida (R$)", format="R$ %.2f", default=0.0),
                "Pago": st.column_config.CheckboxColumn("Pagou?", default=False),
                "Copo_ML_Hoje": st.column_config.NumberColumn("ML Hoje", disabled=True, default=0)
            },
            key="editor_principal"
        )

        # Botão Salvar Tabela
        if st.button("💾 Salvar Alterações na Lista"):
            # Tratamento de erro: Preencher vazios caso o usuário tenha criado linha nova
            df_editado["Divida"] = df_editado["Divida"].fillna(0.0)
            df_editado["Pago"] = df_editado["Pago"].fillna(False)
            df_editado["Copo_ML_Hoje"] = df_editado["Copo_ML_Hoje"].fillna(0)
            
            salvar_dados(df_editado, FILE_USUARIOS)
            st.success("Lista atualizada!")
            st.rerun()

    with col_b:
        st.markdown("### Ferramentas")
        st.write(f"**Custo Galão:** R$ {novo_preco:.2f}")
        
        # Adicionar Cota em Massa
        nomes_lista = df_users[df_users['Nome'].notna()]['Nome'].tolist()
        devedores = st.multiselect("Cobrar de:", nomes_lista)
        valor_add = st.number_input("Valor (R$)", value=5.0)
        
        if st.button("➕ Adicionar Dívida"):
            if devedores:
                # Carrega o estado mais recente (caso tenha editado na tabela antes)
                df_atual = df_editado 
                mask = df_atual['Nome'].isin(devedores)
                df_atual.loc[mask, 'Divida'] += valor_add
                df_atual.loc[mask, 'Pago'] = False
                salvar_dados(df_atual, FILE_USUARIOS)
                st.success("Valores lançados!")
                st.rerun()

# === ABA 2: GAMIFICAÇÃO ===
