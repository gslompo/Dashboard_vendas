import streamlit as st
import requests
import pandas as pd
import plotly as px
import plotly.express as px

#Define um layout mais amplo e evita sobreposições de gráficos, respeitando o tamanho da coluna.
st.set_page_config(layout='wide') 

# Título no Streamlit do dashboard
st.title('DASHBOARD DE VENDAS :shopping_trolley:')

#Essa função formata valores numéricos para torná-los mais legíveis, adicionando unidades como "mil" e "milhões. 
#Depois, passa a formata_numero dentro de cada métrica.
#Desafio: colocar uma métrica ao lado da outra e com duas casas decimais informando mil ou milhões
def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# Requisição de dados
url = 'https://labdados.com/produtos' #Os dados estão no formato json.
regioes=['Brasil', 'Centro_oeste', 'Nordeste','Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')#Aqui estou colocando um titulo para a barra lateral

#FILTRO REGIAO
regiao = st.sidebar.selectbox('Região', regioes) #criando selectbox para região na barra lateral


if regiao == 'Brasil': #se não for selecionada nenhuma região aparece brasil
   regiao = ''

#FILTRO ANO
todos_anos=st.sidebar.checkbox('Dados de todo o período', value=True)
if todos_anos: #se a marcação do checkbox estiver assinalada, não faço nenhuma filtragem de ano
    ano=''
else:
    ano=st.sidebar.slider('Ano', 2020, 2023)##se a marcação do checkbox NÃO estiver assinalada, faço um slider

query_string={'regiao':regiao.lower(), 'ano':ano}#região.lower é para corrigir as letras maiusculas das regiões na url
response = requests.get(url, params = query_string) #acesso aos dados API
dados = pd.DataFrame.from_dict(response.json())#Transformar a requisição para json e gerar um dataframe
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y') #define o formato para datetime para a coluna data da compra.

#FILTRO VENDEDORES

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())#'Vendedores' é o título do filtro que aparece na interface.dados['Vendedor'].unique() gera uma lista única de vendedores disponíveis no DataFrame .
#agora será feita uma configuração para que nas situações em que nenhum vendedor seja selecionado, apareçam todos os vendedores
if filtro_vendedores:#Verifica se há vendedores selecionados
    dados=dados[dados['Vendedor'].isin(filtro_vendedores)]#Filtra o DataFrame para manter apenas os vendedores escolhidos
##TABELAS

## RECEITA ESTADOS
receitas_estados = (dados.groupby('Local da compra')[['Preço']].sum())  #Soma os preços por estado(local da compra).Contruimos nova a tabela mas perdemos a informação de longitude e latitude.
receitas_estados = (dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']]#Mantém apenas uma entrada por local com as coordenadas.
    .merge(receitas_estados, left_on='Local da compra', right_index=True)#Adiciona as receitas ao DataFrame de coordenadas.
    .sort_values('Preço', ascending=False)) #Organiza os locais em ordem decrescente de receita.

## RECEITA MENSAL
# Agora, agrupa os dados corretamente
# Certifique-se de que 'Data da Compra' está no formato correto
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y', errors='coerce')
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index() #Agrupa os dados pela frequência mensal e soma os preços para cada mês.
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year #Cria uma nova coluna de ano no dataframe receita mensal
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name() #Cria uma nova coluna de mês no dataframe receita mensal

##RECEITA CATEGORIAS
receita_categorias=dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

##TABELA QUANTIDADE DE VENDAS


#TABELA VENDEDORES
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))#essa tabela agrupa os dados dos vendedores e a soma de receita

#TABELA QUANTIDADE DE VENDAS POR ESTADO
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count()) #Conta a quantidade de preços por estado(local da compra) para descobrir a quantidade de vendas.Contruimos nova a tabela mas perdemos a informação de longitude e latitude.
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

#TABELA VENDAS MENSAL
vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

#TABELA VENDAS POR CATEGORIA
vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))

## GRAFICOS

#GRAFICO DE MAPA PARA A RECEITA
fig_mapa_receita = px.scatter_geo(receitas_estados,#tabela utilizada para construção do grafico
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',  # mostrar apenas america do sul
                                  size='Preço', #tamanho do circulo do gráfico
                                  template='seaborn',#formato visual do grafico
                                  hover_name='Local da compra',#Quando passa o mouse em cima aparece o estado
                                  hover_data={'lat': False, 'lon': False},#oculta as informações de longitude e latitude
                                  title='Receita por estado')  # Título do gráfico

#MAPA RECEITA MENSAL
fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mês',
                             y = 'Preço',
                             markers = True, #identifica o mes com um pontinho
                             range_y = (0, receita_mensal.max()),#fazer com que o gráfico comece em 0
                             color = 'Ano', #altera a cor conforme ano
                             line_dash = 'Ano',#altera a linha conforme o ano
                             title='Receita Mensal')# Título do gráfico

fig_receita_mensal.update_layout(yaxis_title='Receita')#altarar o título do gráfico de Preço para receita no eixo y.

#MAPA RECEITA POR ESTADOS(BARRA)
fig_receita_estados=px.bar(receitas_estados.head(),#head para aparecer apenas os primeiros 5
                          x='Local da compra',
                          y='Preço',
                          text_auto=True,#Define que os textos do gráfico aparecem de forma automática
                          title='Top Estados(receita)')

fig_receita_estados.update_layout(yaxis_title='Receita')#altera o nome do eixo y

#MAPA RECEITA POR CATEGORIAS(BARRA)
### não precicou passar o X e o Y porque a tabela receita categorias so tem essas duas informações
fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title='Receita por categoria')

fig_receita_categorias.update_layout(yaxis_title='Receita')#Altera a nomenclatura do eixo Y de preço para receita

#MAPA QUANTIDADE DE VENDAS POR ESTADO

fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                     lat = 'lat', 
                     lon= 'lon', 
                     scope = 'south america', 
                     #fitbounds = 'locations', 
                     template='seaborn', 
                     size = 'Preço', 
                     hover_name ='Local da compra', 
                     hover_data = {'lat':False,'lon':False},
                     title = 'Vendas por estado',
                     )

#GRAFICO DE LINHAS COM A QUANTIDADE DE VENDAS MENSAL

fig_vendas_mensal = px.line(vendas_mensal, 
              x = 'Mes',
              y='Preço',
              markers = True, 
              range_y = (0,vendas_mensal.max()), 
              color = 'Ano', 
              line_dash = 'Ano',
              title = 'Quantidade de vendas mensal')

fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

#GRAFICO DE BARRAS COM CONTENDO OS 5 ESTADOS COM MAIOR QUANTIDADE DE VENDAS

fig_vendas_estados = px.bar(vendas_estados.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados'
)

fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

#GRAFICO DE BARRAS COM A QUANTIDADE DE VENDAS POR CATEGORIAS DE PRODUTOS

fig_vendas_categorias = px.bar(vendas_categorias, 
                                text_auto = True,
                                title = 'Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')


aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2=st.columns(2)
    with coluna1:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))#Receita total: soma da coluna preço.
        st.plotly_chart(fig_mapa_receita, use_container_width=True)#coloca o mapa da receita dentro da coluna 1.use_container_width respeita o tamanho do conteiner.
        st.plotly_chart(fig_receita_estados, use_container_width=True)

    with coluna2:
        st.metric('Quantidade de vendas',formata_numero(dados.shape[0]))#shape retorna a quantidade de linhas e colunas do dataframe
        st.plotly_chart(fig_receita_mensal, use_container_width=True)#coloca o mapa da receita_estados dentro da coluna 1.
        st.plotly_chart(fig_receita_categorias,use_container_width=True)


with aba2:
    coluna1, coluna2=st.columns(2)
    with coluna1:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))#Receita total: soma da coluna preço.
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True)
      
    with coluna2:
        st.metric('Quantidade de vendas',formata_numero(dados.shape[0]))#shape retorna a quantidade de linhas e colunas do dataframe
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_categorias, use_container_width = True)

with aba3:
    qtd_vendedores=st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2=st.columns(2)
    with coluna1:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))#Receita total: soma da coluna preço.
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores), #da tabela vendedores, seleciono apenas o sum que é a coluna qu eme interessa E ordenar os dados do maior para o menor.
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,#index para selecionar o nome dos vendedores
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)
     

    with coluna2:
        st.metric('Quantidade de vendas',formata_numero(dados.shape[0]))#shape retorna a quantidade de linhas e colunas do dataframe
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores), #da tabela vendedores, seleciono apenas o sum que é a coluna qu eme interessa E ordenar os dados do maior para o menor.
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,#index para selecionar o nome dos vendedores
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)')   
        st.plotly_chart(fig_vendas_vendedores)






#st.dataframe(dados)#mostrar o dataframe no aplicativo



