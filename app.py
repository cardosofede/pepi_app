import io

import requests
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

st.set_page_config(layout="wide")  # Set the layout to wide


def read_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df


def get_first_image_url(url):
    # Send HTTP request
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

    # Parse HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the first image URL
    for img in soup.find_all('img'):
        img_url = img.get('src')
        if img_url and 'http' in img_url:
            return img_url

    return None


@st.cache_data
def process_data(dataframe):
    # Initialize a new column for image URLs
    dataframe['Image URL'] = ''
    dataframe["PRECIO"] = pd.to_numeric(dataframe["PRECIO"], errors='coerce')

    for index, row in dataframe.iterrows():
        sku = row['CODIGO']
        product = row['PRODUCTO']
        query = sku + ' ' + product
        url = f"https://www.google.com/search?hl=en&tbm=isch&q={'+'.join(query.split())}"
        dataframe.at[index, "URL"] = url
        image_url = get_first_image_url(url)
        if image_url:
            # Append the image URL to the dataframe
            dataframe.at[index, 'Image URL'] = image_url
        else:
            st.error(f"No image found for SKU: {sku}")

    dataframe["selected"] = [False for _ in range(len(dataframe))]
    return dataframe


st.title('💄💋Pepi App')

uploaded_file = st.file_uploader("Choose an Excel file")
if uploaded_file is not None:
    dataframe = read_excel(uploaded_file)
    dataframe = dataframe[["CODIGO", "PRODUCTO", "PRECIO", "SHADE"]]

    if 'CODIGO' in dataframe.columns:
        st.markdown('---')
        dataframe = process_data(dataframe)
        st.write('Displaying the processed data...')
        edited_df = st.data_editor(
            dataframe,
            column_config={
                "Image URL": st.column_config.ImageColumn(
                    "Preview Image", help="Streamlit app preview screenshots", width="large",
                ),
                "URL": st.column_config.LinkColumn(
                    "Google Search URL", help="Google search URL for the product", width="large",)
            },
            use_container_width=True,
            height=400,
            hide_index=True,
        )
        st.markdown('---')
        st.write('Selected data:')
        selected_data = edited_df[edited_df["selected"]][["CODIGO", "PRODUCTO", "PRECIO", "SHADE", "Image URL"]]
        st.dataframe(selected_data, use_container_width=True,
                     column_config={
                         "Image URL": st.column_config.ImageColumn(
                             "Preview Image", help="Streamlit app preview screenshots", width="large",
                         )
                     }, )
        st.write("Total ($): ", selected_data["PRECIO"].sum())
        export_button = st.button("Export selected data to Excel")
        if export_button:
            # Convert DataFrame to Excel
            towrite = io.BytesIO()
            data_to_download = edited_df.copy()
            data_to_download["ELEGIDOS"] = data_to_download["selected"].apply(lambda x: "X" if x else "")
            data_to_download = data_to_download.drop(columns=["selected", "Image URL", "URL"])
            data_to_download.to_excel(towrite, index=False)  # Write to a BytesIO buffer
            towrite.seek(0)  # Go back to the beginning after writing

            # Create a download link
            st.download_button(
                label="Download Excel",
                data=towrite,
                file_name="selected_data.xlsx",
                mime="application/vnd.ms-excel"
            )
            st.success("Data ready for download!")
    else:
        st.error("No 'CODIGO' column found in the Excel file.")
