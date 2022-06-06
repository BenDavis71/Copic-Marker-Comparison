import numpy as np
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
from skimage import color
import streamlit as st
from streamlit_drawable_canvas import st_canvas

#read-in copic marker data data
#cache this function so that streamlit doesn't rerun it everytime a user input is changed
@st.cache(allow_output_mutation=True)
def get_copic_colors():
    return pd.read_parquet('https://github.com/BenDavis71/Copic-Marker-Comparison/blob/main/copic_colors.parquet?raw=true')

#function to convert rgb to hex
def rgb2hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

#title
st.title('Copic Marker Color Picker')
st.markdown('_Click on user-provided image in order to identify 5 closest copic marker colors_')

#canvas variables
stroke_width = 0
point_display_radius = 1
max_height = 650
max_width = 800

#
url = st.text_input("Image URL")
if url:
    response = requests.get(url)
    background_image = Image.open(BytesIO(response.content))
    st.image(background_image)

    #get default width and height
    width, height = background_image.size
    
    # Create a canvas component
    canvas_result1 = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",  # Fixed transparent fill color
        stroke_width=stroke_width,
        point_display_radius=point_display_radius,
        background_image=background_image,
        update_streamlit=True,
        drawing_mode='point',
        height = height,
        width = width,
        key=f'{url}',
    )

    #if necessary, resize image to fit browser window
    if height > max_height:
        ratio = width/height
        height = max_height
        width = int(max_height * ratio)

    if width > max_width:
        ratio = height/width
        width = max_width
        height = int(max_width * ratio)

    background_image = background_image.resize((width, height))

    # Create a canvas component
    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",  # Fixed transparent fill color
        stroke_width=stroke_width,
        point_display_radius=point_display_radius,
        background_image=background_image,
        update_streamlit=True,
        drawing_mode='point',
        height = height,
        width = width,
        key=f'{url}',
    )

    #failure isn't a huge deal since this is a web app with an audience of one (my brother), so I'm just throwing it into a try/except block
    try:
        #get the rgb, hex, and lab color of the latest mouse click
        pixel_df = pd.json_normalize(canvas_result.json_data["objects"])
        pixel_df = pixel_df.iloc[-1:]

        selected_rgb = background_image.getpixel((pixel_df['left'].iloc[0], pixel_df['top'].iloc[0]))
        selected_hex = rgb2hex(*selected_rgb)
        selected_lab = color.rgb2lab([v/255 for v in selected_rgb])

        st.subheader('Selected color + the five closest Copic markers') 

        st.color_picker('Selected Color', selected_hex)

        #find the difference (delta E) between of all the copic markers colors and the selected color
        #then sort by the smallest distance and print the first 5 colors 
        copic_df = get_copic_colors()
        copic_df['difference'] = copic_df['lab'].apply(lambda x: color.deltaE_ciede2000(x,selected_lab))
        copic_df = copic_df.sort_values(by = 'difference', ascending=True, ignore_index=True)

        for i in range(5):
            st.color_picker(f"{copic_df['marker_name'].iloc[i].upper()}", f"{copic_df['hex'].iloc[i]}")


    except:
        st.write('Click anywhere on the photo to analyze its color')


st.markdown('___')
st.markdown('Created by [Ben Davis](https://github.com/BenDavis71/)')
