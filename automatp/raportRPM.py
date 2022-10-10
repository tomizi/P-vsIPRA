# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 10:26:57 2022

@author: tzielinski
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import openpyxl
import xlsxwriter
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb

st.set_page_config(page_title='Raport RPM RKMH', page_icon = ':page_facing_up:', layout='wide')

st.set_option('deprecation.showfileUploaderEncoding',False)

st.title(':page_with_curl: Raport RPM RKMH')

st.sidebar.subheader(':open_file_folder: Wprowadź pliki')

###
file = st.sidebar.file_uploader(label='Raport promocji lokalnych', type=['xlsx'])
###

if file is not None:
    
    try:
        rkmh = pd.read_excel(file,skiprows=[0,1,2,3,4,5])
        rkmh1=rkmh[~rkmh['Opis'].isin(['Nowa_IPRA','RPM on-line - GRUPONY'])]
        piv = pd.pivot_table(rkmh1,values='Wartość sprzedaży',index='Zlecający promocję A',columns='Nazwa prod. sprzedaży',aggfunc=np.sum).fillna(0)
        piv = piv.reindex(index=['Anna Kruczkowska','Anna Słomka','Edyta Gromadzka','Ewa Domagała','Emilia Kulesza','Halina Lindner','Iwona Molka','Iwona Ratajczak','Joanna Miłoszewska','Katarzyna Kiljańska','Paulina Jukiel','Sylwia Kwasigroch','Paweł Werk','Roman Walkowski',
                   'Justyna Jaje','Daniel Matyla'])
        Suma_końcowa = dict()
        a = 0
        for i in piv.columns:
            Suma_końcowa[str(i)]=sum(piv[str(i)])
        piv.loc['Suma końcowa'] = Suma_końcowa
        #st.dataframe(piv.style.format('{:.2f}'))
        piv=piv.reset_index()
        st.dataframe(piv.style.format({piv.columns[1:]:'{:.2f}'}))
        st.download_button(label = 'Pobierz Raport RPM PKMH', data = piv.to_csv(index=False,encoding = 'utf-8'),file_name = 'Raport RPM RKMH.csv', mime = "text/csv")

    except Exception as e:
            st.write('Czekam na dane',e)
