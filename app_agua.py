import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Hidratação Marketing", page_icon="💧", layout="wide")

# --- FUNÇÕES DE MEMÓRIA (PERSISTÊNCIA) ---
# Arquivos CSV para servir de banco de dados simples
FILE_USUARIOS = 'usuarios.csv'
FILE_ESTOQUE = 'estoque.csv'

def carregar_dados_usuarios():
    if not os.path.exists(FILE_USUARIOS):
        # Cria dataframe inicial se não existir
        df = pd.DataFrame(columns=["Nome", "Divida", "Pago", "Copo_ML_Hoje"])
        df.to_csv(FILE_USUARIOS, index=False)
        return df
    return pd.read_csv(FILE_USUARIOS)

def carregar_dados_estoque():
    if not os.path.exists(FILE_ESTOQUE):
        # Cria dados iniciais de estoque
        data = {
            "Preco_Galao": [15.0],
            "Cheios": [2],
            "Vazios": [1],
            "Pedido_Feito": [False],
            "Data_Pedido": ["N/A"]
        }
        df = pd.DataFrame(data)
        df.to_csv(FILE_ESTOQUE, index=False)
        return df
    return pd.read_csv(FILE_ESTOQUE)

def salvar_usuarios(df):
    df.to_csv(FILE_USUARIOS, index=False)

def salvar_estoque(df):
    df.to_csv(FILE_ESTOQUE, index=False)

# --- CARREGAR DADOS ---
df_users = carregar_dados_usuarios()
df_estoque = carregar_dados_estoque()

st.title("💧 Cota da Água & Gamificação - Marketing")

# --- SIDEBAR: ESTOQUE E CONFIGURAÇÕES ---
st.sidebar.header("📦 Gestão de Estoque")

# Edição de Valores do Estoque
novo_preco = st.sidebar.number_input("Preço do Galão (R$)", value=float(df_estoque.at[0, 'Preco_Galao']))
cheios = st.sidebar.number_input("Galões Cheios", value=int(df_estoque.at[0, 'Cheios']), step=1)
vazios = st.sidebar.number_input("Galões Vazios/Secos", value=int(df_estoque.at[0, 'Vazios']), step=1)

# Status do Pedido
st.sidebar.markdown("---")
st.sidebar.subheader("Status do Pedido")
ja_pediu = st.sidebar.checkbox("Pedido realizado?", value=bool(df_estoque.at[0, 'Pedido_Feito']))

if ja_pediu and not df_estoque.at[0, 'Pedido_Feito']:
    # Se acabou de marcar que pediu, salva a data de hoje
    data_pedido = datetime.now().strftime("%d/%m/%Y %H:%M")
else:
    data_pedido = df_estoque.at[0, 'Data_Pedido']

st.sidebar.info(f"Último pedido: {data_pedido}")

# Botão Salvar Estoque
if st.sidebar.button("Atualizar Estoque"):
    df_estoque.at[0, 'Preco_Galao'] = novo_preco
    df_estoque.at[0, 'Cheios'] = cheios
    df_estoque.at[0, 'Vazios'] = vazios
    df_estoque.at[0, 'Pedido_Feito'] = ja_pediu
    df_estoque.at[0, 'Data_Pedido'] = data_pedido
    salvar_estoque(df_estoque)
    st.sidebar.success("Estoque atualizado!")
    st.rerun() # Recarrega a página

# --- ÁREA PRINCIPAL ---
tab1, tab2 = st.tabs(["💰 Financeiro & Pessoas", "🏆 Gamificação (Quem bebe mais?)"])

with tab1:
    st.subheader("Lista do Time e Pagamentos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Exibição da Tabela Editável
        edited_df = st.data_editor(
            df_users,
            column_config={
                "Pago": st.column_config.CheckboxColumn("Já Pagou?", help="Marque se a pessoa pagou a cota"),
                "Divida": st.column_config.NumberColumn("Dívida (R$)", format="R$ %.2f"),
                "Copo_ML_Hoje": st.column_config.NumberColumn("Ml Bebidos", disabled=True) # Não edita aqui, só na gamificação
            },
            num_rows="dynamic", # Permite adicionar linhas (novas pessoas)
            key="editor_usuarios"
        )
        
        if st.button("Salvar Alterações na Lista"):
            salvar_usuarios(edited_df)
            st.success("Lista atualizada com sucesso!")
    
    with col2:
        st.markdown("### Ferramentas Rápidas")
        # Rateio rápido
        st.info(f"O galão custa R${novo_preco:.2f}")
        pessoas_para_cobrar = st.multiselect("Adicionar dívida para:", df_users['Nome'].tolist())
        valor_cobranca = st.number_input("Valor a adicionar (R$)", value=5.00, step=0.50)
        
        if st.button("Adicionar Cota"):
            if pessoas_para_cobrar:
                mask = df_users['Nome'].isin(pessoas_para_cobrar)
                df_users.loc[mask, 'Divida'] += valor_cobranca
                df_users.loc[mask, 'Pago'] = False # Reseta o status de pago se aumentou dívida
                salvar_usuarios(df_users)
                st.success("Valores adicionados!")
                st.rerun()
            else:
                st.warning("Selecione alguém.")

with tab2:
    st.subheader("Hidratação do Time 🥤")
    st.caption("Meta diária: 2000ml (2 Litros)")
    
    col_game1, col_game2 = st.columns([1, 2])
    
    with col_game1:
        st.markdown("#### Registrar Bebida")
        bebedor = st.selectbox("Quem está bebendo?", df_users['Nome'].tolist())
        qtd_ml = st.radio("Quantidade:", [200, 300, 500], horizontal=True)
        
        if st.button("Beber Água! 🌊"):
            idx = df_users[df_users['Nome'] == bebedor].index
            if not idx.empty:
                df_users.loc[idx, 'Copo_ML_Hoje'] += qtd_ml
                salvar_usuarios(df_users)
                st.balloons() # Efeito visual divertido
                st.success(f"{qtd_ml}ml adicionados para {bebedor}!")
            
            # Botão para zerar o dia (pode ser automático via script, mas aqui manual para simplicidade)
        st.markdown("---")
        if st.button("Zerar Contador Diário (Novo Dia)"):
             df_users['Copo_ML_Hoje'] = 0
             salvar_usuarios(df_users)
             st.warning("Contadores zerados para o novo dia.")
             st.rerun()

    with col_game2:
        st.markdown("#### Ranking do Dia")
        if not df_users.empty:
            # Ordena do maior para o menor
            df_rank = df_users.sort_values(by="Copo_ML_Hoje", ascending=False)
            
            # Gráfico de Barras Simples
            st.bar_chart(df_rank, x="Nome", y="Copo_ML_Hoje", color="#00a8cc")
            
            # Líder
            lider = df_rank.iloc[0]
            if lider['Copo_ML_Hoje'] > 0:
                st.markdown(f"👑 **Líder Atual:** {lider['Nome']} com {lider['Copo_ML_Hoje']}ml")
            else:
                st.info("Ninguém bebeu água ainda hoje!")