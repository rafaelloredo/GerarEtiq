import streamlit as st
from database import *
from serial_generator import gerar_numero_serie
from etiqueta import gerar_etiqueta_pdf
from datetime import datetime, time
import os
import base64

# =========================
# INICIALIZA ESTADO DE SESSÃO
# =========================
if "reimprimir_serie" not in st.session_state:
    st.session_state.reimprimir_serie = None

# =========================
# INTERFACE PRINCIPAL SEM LOGIN
# =========================
st.sidebar.markdown(f"👤 Acesso Livre")
opcao = st.sidebar.selectbox("Escolha a operação:", ["Gerar Série", "Consultar Série", "Cadastrar Produto"])

def tela_cadastro_produto():
    st.subheader("Cadastro de Produto")
    codigo = st.text_input("Código do Produto")
    nome = st.text_input("Nome do Produto")
    descricao = st.text_area("Descrição")
    if st.button("Cadastrar"):
        if codigo and nome:
            cadastrar_produto(codigo, nome, descricao)
            st.success("✅ Produto cadastrado com sucesso!")
        else:
            st.warning("Preencha ao menos o código e nome do produto.")

def tela_gerar_serie():
    st.subheader("Gerar Número de Série")
    codigo = st.text_input("Digite o Código do Produto")
    quantidade = st.number_input("Quantidade de Números de Série", min_value=1, step=1, value=1)
    tamanho = st.selectbox("Tamanho da Etiqueta", ["Pequena", "Média", "Grande", "Dupla"], index=3)
    if "arquivos_pdf" not in st.session_state:
        st.session_state.arquivos_pdf = []
    if st.button("Gerar Série"):
        produto = buscar_produto(codigo)
        if produto:
            series_geradas = []
            for _ in range(quantidade):
                numero_serie = gerar_numero_serie(codigo)
                data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                salvar_serie(codigo, numero_serie, data)
                series_geradas.append(numero_serie)
            arquivos = gerar_etiqueta_pdf(produto, series_geradas, tamanho)
            st.session_state.arquivos_pdf = arquivos
            st.success(f"{quantidade} número(s) de série gerado(s) com sucesso!")
        else:
            st.warning("⚠️ Produto não encontrado. Cadastre-o primeiro.")
    if st.session_state.arquivos_pdf:
        for arquivo in st.session_state.arquivos_pdf:
            with open(arquivo, "rb") as file:
                st.download_button(
                    label=f"📅 Baixar {os.path.basename(arquivo)}",
                    data=file,
                    file_name=os.path.basename(arquivo),
                    mime="application/pdf"
                )

def tela_consultar_serie():
    st.subheader("Consulta de Números de Série")
    codigo = st.text_input("Código do Produto")
    data_inicio = st.date_input("Data Inicial")
    data_fim = st.date_input("Data Final")
    numero_serie_input = st.text_input("Buscar por Número de Série")
    pagina = st.number_input("Página", min_value=1, step=1, value=1)
    if st.button("Consultar") or codigo:
        filtros = {}
        if data_inicio:
            filtros['data_inicio'] = datetime.combine(data_inicio, time.min).strftime("%Y-%m-%d %H:%M:%S")
        if data_fim:
            filtros['data_fim'] = datetime.combine(data_fim, time.max).strftime("%Y-%m-%d %H:%M:%S")
        if numero_serie_input:
            filtros['numero_serie'] = numero_serie_input
        todas_series = consultar_series(codigo_produto=codigo, **filtros)
        if todas_series:
            total_paginas = (len(todas_series) + 49) // 50
            inicio = (pagina - 1) * 50
            fim = inicio + 50
            series_pagina = todas_series[inicio:fim]
            st.markdown(f"📄 Mostrando página **{pagina}** de **{total_paginas}**")
            for idx, serie in enumerate(series_pagina):
                numero_serie = serie["numero_serie"]
                data_geracao = serie["data_geracao"]
                unique_id = f"{codigo}_{numero_serie}_{idx}"
                col1, col2, col3 = st.columns([3, 1.5, 1.5])
                with col1:
                    st.write(f"📦 Nº Série: {numero_serie}\n\n🕒 Gerado em: {data_geracao}")
                with col2:
                    tamanho_individual = st.selectbox(
                        "Tamanho", ["Pequena", "Média", "Grande", "Dupla"], index=3, key=f"selectbox_{unique_id}"
                    )
                    if st.button("Reimprimir", key=f"reimprimir_{unique_id}"):
                        st.session_state.reimprimir_serie = (codigo, numero_serie, idx, tamanho_individual)
                with col3:
                    if (
                        st.session_state.reimprimir_serie
                        and st.session_state.reimprimir_serie[:3] == (codigo, numero_serie, idx)
                    ):
                        produto = buscar_produto(codigo)
                        tamanho_individual = st.session_state.reimprimir_serie[3]
                        if produto:
                            caminho = gerar_etiqueta_pdf(produto, [numero_serie], tamanho_individual)[0]
                            with open(caminho, "rb") as file:
                                st.download_button(
                                    label="⬇️ Baixar",
                                    data=file,
                                    file_name=os.path.basename(caminho),
                                    mime="application/pdf",
                                    key=f"download_{unique_id}"
                                )
        else:
            st.warning("❌ Nenhum número de série encontrado para os critérios.")

# Exibe a tela de acordo com a escolha no menu lateral
if opcao == "Cadastrar Produto":
    tela_cadastro_produto()
elif opcao == "Gerar Série":
    tela_gerar_serie()
elif opcao == "Consultar Série":
    tela_consultar_serie()

