# -*- coding: utf-8 -*-
"""
Created on Thu Sep 15 11:48:36 2022

@author: User
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import openpyxl
import xlsxwriter
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb

st.set_option('deprecation.showfileUploaderEncoding',False)

st.title(':page_with_curl: Raport P+ vs IPRA')

st.sidebar.subheader(':open_file_folder: Wprowadź pliki')

###
rap_prom = st.sidebar.file_uploader(label='Raport Promocji', type=['csv'])
ipra = st.sidebar.file_uploader(label='IPRA z ostatniego miesiąca', type=['xlsx'])
###
if rap_prom is not None or ipra is not None:
    
    try:
        ###
        plik = pd.read_csv(rap_prom,sep=';',dtype={'Rabat Promocyjny':'str'})
        ###
        
        ###
        IPRA_BWH = pd.read_excel(ipra,sheet_name='IPRA BWH')
        IPRA_WHA = pd.read_excel(ipra,sheet_name='IPRA WHA')
        IPRA_EO  = pd.read_excel(ipra,sheet_name='IPRA EO IX')
        ###
        
        ###
        IPRA_BWH = IPRA_BWH.sort_values(by=['Indeks','Rabat IPRA'], ignore_index=True)
        IPRA_BWH = IPRA_BWH.drop_duplicates(subset='Indeks',keep='last', inplace=False, ignore_index=True)
        
        IPRA_WHA = IPRA_WHA.sort_values(by=['Indeks','Rabat IPRA'], ignore_index=True)
        IPRA_WHA = IPRA_WHA.drop_duplicates(subset='Indeks',keep='last', inplace=False, ignore_index=True)
        
        IPRA_EO = IPRA_EO.sort_values(by=['Indeks','Rabat IPRA'], ignore_index=True)
        IPRA_EO = IPRA_EO.drop_duplicates(subset='Indeks',keep='last', inplace=False, ignore_index=True)
        ###
        
        ############################################################
        ### Nazwy kolumn, które mają zostać
        kolumny=['Nazwa Promocji','Nr producenta sprzedażowego','Nazwa producenta sprzedażowego',
                 'Skład (SPR,SGL)','Czy dopuszcza rabat kontraktowy','Id Materiału','Nazwa Materiału',
                 'Rabat Promocyjny','Cena z cennika głównego','identyfikator promocji','data obowiązywania promocji od',
                 'Data obowiązywania promocji do','Rodzaj warunku płatnosci','Ilość Klientów','Nazwa grupy promocyjnej',
                 'MPK','Grupa klientów','Czy KDW']
        
        ### Lista kolumn, które chcemy usunąć
        lista = list(set(plik.columns) - set(kolumny))
        
        ### Usuwamy te kolumny
        plik = plik.drop(lista,axis=1)
        
        ### Zamieniamy kolejność kolumn na taką jaka powinna być
        plik = plik.loc[:,kolumny]
        
        ### Selekcjonujemy wszystko co zawiera P+ i Partner +
        plik1=plik[plik['Nazwa Promocji'].str.contains(pat='P+',regex=False) |
                   plik['Nazwa Promocji'].str.contains(pat='PARTNER+',regex=False)]
        
        ### Resetujemy indeksy (znowu są od 1 do n po koleji)
        plik1=plik1.reset_index(drop=True)
        
        ###zamieniamy NaN na 0
        plik1 = plik1.fillna('0,0')
        ### Modyfikujemy rabat promocyjny na format procentowy
        def zamiana(data):
            data = data.replace(",", "[]").replace(".", ",").replace("[]", ".")
            return data
        
        plik1['Rabat Promocyjny'] = [zamiana(i) for i in plik1['Rabat Promocyjny']]
        plik1['Rabat Promocyjny'] = plik1['Rabat Promocyjny'].astype(float)
        plik1['Rabat Promocyjny'] = -plik1['Rabat Promocyjny']/100
        
        
        ### SGL, Standard, Ilość klientów >= 1000, PARTNER_PLUS_MEDIQ :D
        plik1=plik1[(plik1["Skład (SPR,SGL)"]=='SGL') &
                    (plik1['Rodzaj warunku płatnosci'] == 'Standard') &
                    (plik1['Ilość Klientów'] >= 1000) & (plik1['Nazwa grupy promocyjnej'] == 'PARTNER_PLUS_MEDIQ')]
        
        ### Rozbijamy na P+ BWH i P+ WHA
        PBWH = plik1[plik1['Czy dopuszcza rabat kontraktowy'] == 0].reset_index(drop = True)
        PWHA = plik1[plik1['Czy dopuszcza rabat kontraktowy'] == 1].reset_index(drop = True)
        
        ### Sortujemy malejącjo po ID Materiału i Rabacie Promocyjnym
        PBWH=PBWH.sort_values(by=['Id Materiału','Rabat Promocyjny'], ignore_index=True)
        PWHA=PWHA.sort_values(by=['Id Materiału','Rabat Promocyjny'], ignore_index=True)
        
        ### Usuwamy duplikaty zostawiając większy rabat
        PBWH=PBWH.drop_duplicates(subset='Id Materiału',keep='last', inplace=False, ignore_index=True)
        PWHA=PWHA.drop_duplicates(subset='Id Materiału',keep='last', inplace=False, ignore_index=True)
        
        ### Doszywamy Rabaty IPRA WHA I BWH I EO z pliku IPRA_MIESIAC_ROK
        PBWH = PBWH.join(IPRA_BWH.iloc[:,[0,6]].set_index('Indeks'),on ='Id Materiału')
        PWHA = PWHA.join(IPRA_WHA.iloc[:,[0,6]].set_index('Indeks'),on ='Id Materiału')
        PWHA=PWHA.rename(columns={'Rabat IPRA':'Rabat IPRA1'}) # tutaj zamieniamy nazwe kolumny żeby się nie powelały
        PWHA = PWHA.join(IPRA_EO.iloc[:,[0,6]].set_index('Indeks'),on ='Id Materiału')
        
        ### 1 tam gdzie IPRA lepsza od P+, tam gdzie gorsza
        PBWH['IPRA BWH vs P+'] = np.where(PBWH['Rabat IPRA'].isna(),None,np.where(PBWH['Rabat IPRA']>=PBWH['Rabat Promocyjny'],1,0))
        PWHA['IPRA WHA vs P+'] = np.where(PWHA['Rabat IPRA1'].isna(),None,np.where(PWHA['Rabat IPRA1']>=PWHA['Rabat Promocyjny'],1,0))
        PWHA['EO vs P+'] = np.where(PWHA['Rabat IPRA'].isna(),None,np.where(PWHA['Rabat IPRA']>=PWHA['Rabat Promocyjny'],1,0))
        
        ### Modyfikacje stylistyczne
        PWHA=PWHA.rename(columns={'Rabat IPRA1':'Rabat IPRA WHA'})
        PWHA=PWHA.rename(columns={'Rabat IPRA':'Rabat EO'})
        PBWH=PBWH.rename(columns={'Rabat IPRA':'Rabat IPRA BWH'})
        
        kolumny_WHA=['Nazwa Promocji','Nr producenta sprzedażowego','Nazwa producenta sprzedażowego',
                 'Skład (SPR,SGL)','Czy dopuszcza rabat kontraktowy','Id Materiału','Nazwa Materiału',
                 'Rabat Promocyjny','Rabat IPRA WHA','Rabat EO','IPRA WHA vs P+','EO vs P+',
                     'Cena z cennika głównego','identyfikator promocji','data obowiązywania promocji od',
                 'Data obowiązywania promocji do','Rodzaj warunku płatnosci','Ilość Klientów','Nazwa grupy promocyjnej',
                 'MPK','Grupa klientów','Czy KDW']
        kolumny_BWH=['Nazwa Promocji','Nr producenta sprzedażowego','Nazwa producenta sprzedażowego',
                 'Skład (SPR,SGL)','Czy dopuszcza rabat kontraktowy','Id Materiału','Nazwa Materiału',
                 'Rabat Promocyjny','Rabat IPRA BWH','IPRA BWH vs P+',
                     'Cena z cennika głównego','identyfikator promocji','data obowiązywania promocji od',
                 'Data obowiązywania promocji do','Rodzaj warunku płatnosci','Ilość Klientów','Nazwa grupy promocyjnej',
                 'MPK','Grupa klientów','Czy KDW']
        
        PWHA = PWHA.loc[:,kolumny_WHA]
        PBWH = PBWH.loc[:,kolumny_BWH]
        
        ### Podsumowanie
        c1 = len(PWHA[(PWHA['IPRA WHA vs P+'] == 0) | (PWHA['IPRA WHA vs P+'] == 1)])
        c2 = len(PBWH[(PBWH['IPRA BWH vs P+'] == 0) | (PBWH['IPRA BWH vs P+'] == 1)])
        c3 = len(PWHA[(PWHA['EO vs P+'] == 0) | (PWHA['EO vs P+'] == 1)])
        
        w1 = len(PWHA[PWHA['IPRA WHA vs P+'] == 1])
        w2 = len(PBWH[PBWH['IPRA BWH vs P+'] == 1])
        w3 = len(PWHA[PWHA['EO vs P+'] == 1])
        podsumowanie = pd.DataFrame({'Podsumowanie:':['część wspólna','wyższy od P+  lub równy rabat IPRA','jaki to procent'],
                                     'P+ WHA':[int(c1),int(w1),100*w1/c1],
                                    'P+ BWH':[int(c2),int(w2),100*w2/c2],
                                    'EO vs P+ WHA':[int(c3),int(w3),100*w3/c3]})
        ############################################################
        st.subheader('P+ vs WHA')
        st.dataframe(PWHA.style.format({'Rabat Promocyjny': '{:.2f}','Rabat IPRA WHA': '{:.2f}','Rabat EO': '{:.2f}'}))
        
        st.subheader('P+ vs BWH')
        st.dataframe(PBWH.style.format({'Rabat Promocyjny': '{:.2f}','Rabat IPRA WHA': '{:.2f}','Rabat EO': '{:.2f}'}))
        
        
        st.subheader('Podsumowanie')
        st.dataframe(podsumowanie.style.format({'P+ WHA': '{:.0f}', 'P+ BWH': '{:.0f}', 'EO vs P+ WHA': '{:.0f}'}))
        
        st.balloons()
        ############################################################
        
        def to_excel():
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            PBWH.to_excel(writer, sheet_name='P+ BWH',index=False)
            PWHA.to_excel(writer, sheet_name='P+ WHA',index=False)
            podsumowanie.to_excel(writer, sheet_name = 'Podsumowanie', index=False)
            workbook = writer.book
            #worksheet = writer.sheets
            format1 = workbook.add_format({'num_format': '0.00'}) 
            #worksheet.set_column('A:A', None, format1)  
            writer.save()
            processed_data = output.getvalue()
            return processed_data
        df_xlsx = to_excel()
        
        data = st.text_input('Podaj dzisiejszą datę',' ')
        st.download_button(label='Pobierz plik "P+ vs IPRA_{}.xlsx"'.format(data),
                                        data=df_xlsx ,
                                        file_name= 'P+ vs IPRA_{}.xlsx'.format(data))
        ############################################################
        st.header('Wizualizacja danych - dodatkowa analiza')
        
        ##
        nowy=PWHA[~PWHA['Rabat IPRA WHA'].isna()]
        nowy
        nowy['Rabat IPRA WHA']=nowy['Rabat IPRA WHA']*100
        nowy['Rabat Promocyjny']=nowy['Rabat Promocyjny']*100
        
        
        ##
        
        nowy1=PBWH[~PBWH['Rabat IPRA BWH'].isna()]
        nowy1
        #nowy1['Rabat IPRA BWH']=nowy['Rabat IPRA BWH']*100
        #nowy1['Rabat Promocyjny']=nowy['Rabat Promocyjny']*100
        ##
        
        '''
        nowy2=PWHA[~PWHA['Rabat EO'].isna()]
        
        nowy2['Rabat EO']=nowy['Rabat EO']*100
        nowy2['Rabat Promocyjny']=nowy['Rabat Promocyjny']*100
        '''
        ##
        '''
        l, m, r = st.columns(3)
        
        with l:
            st.plotly_chart(px.scatter(nowy,x='Rabat IPRA WHA',y='Rabat Promocyjny').update_layout(
            shapes=[
                dict(
                    type= 'line',
                    yref= 'y', y0=0, y1= 50,
                    xref= 'x', x0=0, x1= 50,
                    opacity = 0.4
                )
            ]))
        
        with m:
            st.plotly_chart(px.scatter(nowy1,x='Rabat IPRA BWH',y='Rabat Promocyjny').update_layout(
            shapes=[
                dict(
                    type= 'line',
                    yref= 'y', y0=0, y1= 50,
                    xref= 'x', x0=0, x1= 50,
                    opacity = 0.4
                )
            ]))
        with r:
            st.plotly_chart(px.scatter(nowy2,x='Rabat EO',y='Rabat Promocyjny').update_layout(
            shapes=[
                dict(
                    type= 'line',
                    yref= 'y', y0=0, y1= 50,
                    xref= 'x', x0=0, x1= 50,
                    opacity = 0.4
                )
            ]))
            
        '''    
        st.plotly_chart(px.histogram(nowy['Rabat Promocyjny'],text_auto=True,marginal='box'))
        
        st.plotly_chart(px.histogram(nowy['Rabat IPRA WHA'],text_auto=True,marginal='box'))
    except Exception as e:
        st.write('Czekam na dane',print(e))
        
