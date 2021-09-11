import streamlit as st
from PIL import Image
from glob import glob
import boto3
import datetime
import os

st.set_page_config(
    page_title='現場状況',
    page_icon='🍅',
)

"""
# ベジデジ
## 現場最新画像閲覧システム
### aeon_rifu_1とaeon_rifu_2
____
"""

s3 = boto3.resource('s3')
bucket = s3.Bucket('vegi-upload-images')
s3 = boto3.client('s3',
                  aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                  aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
                  region_name='ap-northeast-1'
                  )


def latest_image_path(store_name, bucket):
    dt = datetime.datetime.now()
    prefix = store_name + dt.strftime("/%Y/%m/%d/")
    response = s3.list_objects(Bucket=bucket, Prefix=prefix)
    if "Contents" in response:
        contents = response["Contents"][-1]
        return contents["Key"]
    else:
        return 0

@st.cache()
def download_image(latest_images):
    for latest_image in latest_images:
        try:
            os.makedirs("./latest_images/", exist_ok=True)
            s3.download_file('vegi-upload-images', latest_image, "./latest_images/"+latest_image.split("/")[-1])
        except:
            st.error(latest_image.split("/")[0]+"の画像をダウンロードできませんでした")

@st.cache()
def read_image():    
    img1 = Image.open("./latest_images/"+latest_image1.split("/")[-1])  
    img2 = Image.open("./latest_images/"+latest_image2.split("/")[-1])  
    return img1, img2


latest_image1 = latest_image_path("aeon_rifu_1", "vegi-upload-images")
latest_image2 = latest_image_path("aeon_rifu_2", "vegi-upload-images")
latest_images = latest_image1, latest_image2

download_image(latest_images)


img1, img2 = read_image()

st.write(latest_image1.split("/")[0])
st.image(img1, caption=latest_image1.split("/")[-1])

st.write(latest_image2.split("/")[0])
st.image(img2, caption=latest_image2.split("/")[-1])



    
