import streamlit as st
import requests
import pandas as pd
import time


#converter arquivo para download csv

@st.cache_data#se a pessoa fez uma vez a conversão, não precisará fazer a conversão todas as vezes. Fica armazenado em cache
def converte_csv(df):
    return df.to_csv(index=False).encode('utf-8') 

def mensagem_sucesso():
    sucesso=st.success('O arquivo foi baixado com sucesso!', icon="✅")
    time.sleep(5)#eliminar mensagem apos 5 minutos
    sucesso.empty()
    
st.title('DADOS BRUTOS')

url = 'https://labdados.com/produtos'

response = requests.get(url)
dados = pd.DataFrame.from_dict(response.json())  # Correção aqui!
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

##Temos várias colunas no Dataframe. Para facilitar a visuaização por parte do usuário vamos colocar acima do DartaFrame
# o filtro para escolher a coluna:

with st.expander('Colunas'):
    colunas = st.multiselect('Selecione as colunas', list(dados.columns),list(dados.columns))

#Agora, vamos colocar filtros laterais(sidebar):
                             
st.sidebar.title('Filtros')#Título do inicio da sequência de filtros
with st.sidebar.expander('Nome do produto'):
    produtos = st.multiselect('Selecione os produtos', dados['Produto'].unique(),dados['Produto'].unique())
with st.sidebar.expander('Preço do Produto'):
    preco = st.slider('Selecione o preço', 0, 5000, (0,5000))#slider é a barrinha de faixa de preços
with st.sidebar.expander('Data da compra'):
    data_compra = st.date_input('Selecione a data',([dados['Data da Compra'].min(), dados['Data da Compra'].max()] ))
with st.sidebar.expander('Categoria do produto'):
    categoria = st.multiselect('Selecione as categorias', dados['Categoria do Produto'].unique(),dados['Categoria do Produto'].unique())
with st.sidebar.expander('Frete da venda'):
    frete = st.slider('Frete', 0,250, (0,250))#slider é a barrinha de faixa de preços
with st.sidebar.expander('Vendedor'):
    vendedores = st.multiselect('Selecione os vendedores', dados['Vendedor'].unique(),dados['Vendedor'].unique())
with st.sidebar.expander('Local da compra'):
    local_compra = st.multiselect('Selecione o local da compra', dados['Local da compra'].unique(), dados['Local da compra'].unique())
with st.sidebar.expander('Avaliacao da compra'):
    avaliacao = st.slider('Selecione a avaliacao da compra', 1, 5, (1,5))
with st.sidebar.expander('Tipo de pagamento'):
    tipo_pagamento = st.multiselect('Selecione o tipo de pagamento', dados['Tipo de pagamento'].unique(),dados['Tipo de pagamento'].unique())
with st.sidebar.expander('Quantidade de parcelas'):
    qtd_parcelas = st.slider('Selecione a quantidade de parcelas', 1,24, (1,24))

#Criamos os filtros mas eles não estão funcionando ainda. Então, vamos fazê-los funcionar usando a biblioteca pandas

query = '''
Produto in @produtos and \
`Categoria do Produto` in @categoria and \
@preco[0] <= Preço <= @preco[1] and \
@frete[0] <= Frete <= @frete[1] and \
@data_compra[0] <= `Data da Compra` <= @data_compra[1] and \
Vendedor in @vendedores and \
`Local da compra` in @local_compra and \
@avaliacao[0]<= `Avaliação da compra` <= @avaliacao[1] and \
`Tipo de pagamento` in @tipo_pagamento and \
@qtd_parcelas[0] <= `Quantidade de parcelas` <= @qtd_parcelas[1]
'''

dados_filtrados = dados.query(query)
dados_filtrados = dados_filtrados[colunas]

st.dataframe(dados_filtrados)
st.markdown(f'A tabela possui :blue[{dados_filtrados.shape[0]}] linhas e :blue[{dados_filtrados.shape[1]}] colchetes')
#st.dataframe(dados)  # Adicionado 'dados' para exibir corretamente na interface

st.markdown('Escreva um nome para o arquivo')#botão de download
coluna1, coluna2 = st.columns(2) #criar duas colunas
with coluna1: #nessa coluna vai ter o nome do arquivo
    nome_arquivo = st.text_input('', label_visibility='collapsed', value='dados')
    nome_arquivo += '.csv'
with coluna2:
    st.download_button('Fazer o download da tabela em csv', data=converte_csv(dados_filtrados),file_name=nome_arquivo, mime='text/csv', on_click=mensagem_sucesso)
