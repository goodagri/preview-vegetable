import streamlit as st
from PIL import Image
from glob import glob
import boto3
import datetime
import os
import shutil
import time

st.set_page_config(
    page_title='現場状況',
    page_icon='🍅',
)

"""
# 🍅ベジデジ
## 現場最新画像閲覧システム
____
"""
stores = ["aeon_rifu_1","aeon_rifu_2"]
bucket_name = "vegi-upload-images"

s3 = boto3.resource('s3')
bucket = s3.Bucket('vegi-upload-images')
s3 = boto3.client('s3',
                  aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                  aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
                  region_name='ap-northeast-1'
                  )


def latest_image_path(store_name, bucket_name):
    dt = datetime.datetime.now()
    prefix = store_name + dt.strftime("/%Y/%m/%d/")
    response = s3.list_objects(Bucket=bucket_name, Prefix=prefix)
    if "Contents" in response:
        contents = response["Contents"][-1]
        return contents["Key"]
    else:
        return 0
        
def get_latest_image_paths(stores, bucket_name):
    latest_image_paths = []
    for store in stores:
        latest_image = latest_image_path(store, bucket_name)
        latest_image_paths.append(latest_image)
    return latest_image_paths

def download_image(latest_images):
    if os.path.isdir("./latest_images/"):
        shutil.rmtree("./latest_images/")
    os.makedirs("./latest_images/", exist_ok=True)
    for latest_image in latest_images:
        try:
            s3.download_file(bucket_name, latest_image, "./latest_images/"+latest_image.split("/")[-1])
        except:
            st.error(latest_image.split("/")[0]+"の画像をダウンロードできませんでした")

def clear_upload_images():    
    LatestImagePaths = get_latest_image_paths(stores, bucket_name)
    download_image(LatestImagePaths)

def main():
    images = glob("./latest_images/"+ "*.jpg")
    for i, image in enumerate(images):
        st.write("端末名：",stores[i])
        pil_img = Image.open(image)
        st.image(pil_img, caption=image.split("/")[-1])


uppdate_button = st.button("最新画像に更新")

if uppdate_button:
    state = st.empty()
    state.write("最新の売り場画像に更新しています....")
    clear_upload_images()
    state.success("更新完了")
    time.sleep(0.5)

main()
