#Script     : NPI Autommation
#Version    : 1.00 | 2023
#Author     : Joeneil S Taguan
#Updated    : Joeneil S Taguan

from PIL import Image

import yaml
from yaml.loader import SafeLoader

import streamlit as st

st.set_page_config(page_title="Web App Demo Page", page_icon=":bar_chart:", layout="wide")

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authentication_status = True

if authentication_status == True:

# ------ Authentication End

    rPc1,rPc2 =st.columns((8,92))
    with rPc1:
        img_p = './visuals/logo.png'
        image = Image.open(img_p)
        new_image = image.resize((140, 80))
        st.image(new_image, caption='')
    with rPc2:
        st.header ("The future of value creation in enterprises...")
    st.write("---")

    r1Pc1,r1Pc2 =st.columns((50,50))
    with r1Pc1:
        img_p = './visuals/p1.png'
        image = Image.open(img_p)
        new_image = image.resize((800, 500))
        st.image(new_image, caption='')
    with r1Pc2:
        img_p = './visuals/p2.png'
        image = Image.open(img_p)
        new_image = image.resize((800, 500))
        st.image(new_image, caption='')

    r2Pc1,r2Pc2 =st.columns((50,50))
    with r2Pc1:
        img_p = './visuals/p3.png'
        image = Image.open(img_p)
        new_image = image.resize((800, 500))
        st.image(new_image, caption='')
    with r2Pc2:
        img_p = './visuals/p4.png'
        image = Image.open(img_p)
        new_image = image.resize((800, 500))
        st.image(new_image, caption='')

    hide_st_style = """
                <style>
                MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)
