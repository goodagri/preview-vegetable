import streamlit as st
from PIL import Image
from glob import glob
import boto3
import datetime
import os
import shutil
import time
import json

st.set_page_config(
    page_title='現場状況',
    page_icon='🍅',
)

"""
# 🍅デジベジ
## 現場最新画像閲覧システム
____
"""
stores = ["aeon_rifu_1","aeon_rifu_2", "aeon_rifu_3", "aeon_rifu_4"]

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
    latest_image_dict = {}
    for store in stores:
        latest_image = latest_image_path(store, bucket_name)
        latest_image_dict[store] = latest_image
    return latest_image_dict

def download_image(latest_image_dict):
    if os.path.isdir("./latest_images/"):
        shutil.rmtree("./latest_images/")
    os.makedirs("./latest_images/", exist_ok=True)
    for store_name, latest_image in latest_image_dict.items():
        try:
            s3.download_file(bucket_name, latest_image, "./latest_images/"+ store_name.replace("_", "-") +"_"+latest_image.split("/")[-1])
        except:
            st.error(f"本日の{store_name}の画像をダウンロードできませんでした")

def clear_upload_images():    
    latest_image_dict = get_latest_image_paths(stores, bucket_name)
    download_image(latest_image_dict)

@st.cache
def read_image(images):
    pil_imgs = []
    for i, image in enumerate(images):
        pil_img = Image.open(image)
        pil_imgs.append(pil_img)
    return pil_imgs

@st.cache
def get_device_list(bucket_name=bucket_name):
    result = bucket.meta.client.list_objects(Bucket=bucket_name, Delimiter='/')
    device_list = []
    for o in result.get('CommonPrefixes'):
        device_list.append(o.get('Prefix').split("/")[0])
    return device_list

def main(images, Pil_Images, stores):
    for i, image in enumerate(images):
        st.markdown("## 端末："+image.split("/")[-1].split(".")[0].split("_")[0])
        time = images[i].split("/")[-1].split(".")[0].split("_")[1:]
        st.markdown("#### 📷撮影時刻："+time[0]+"年"+time[1][:2]+"月"+time[1][2:]+"日"+time[2][:2]+"時"+time[2][2:4]+"分")
        st.image(Pil_Images[i], caption=images[i].split("/")[-1])
        st.markdown("___")

uppdate_button = st.button("最新画像に更新")
device_list = get_device_list()
stores = st.multiselect(
    "端末を選ぶ",
    device_list,
    ["aeon_rifu_1","aeon_rifu_2", "aeon_rifu_3", "aeon_rifu_4"]
    )

# with st.form(key='my_form'):

#     stores = st.multiselect(
#         "端末を選ぶ",
#         device_list,
#         ["aeon_rifu_1","aeon_rifu_2", "aeon_rifu_3", "aeon_rifu_4"]
#         )
# 	submit_button = st.form_submit_button('Submit')

# if submit_button:
#     with open("./devices.json", "w") as f:
#         devices_dict = {"device":device_list}
#         json.dump(devices_dict, f)

if uppdate_button:
    state = st.empty()
    state.write("最新の売り場画像に更新しています....")
    clear_upload_images()
    state.success("更新完了")

images = glob("./latest_images/"+ "*.jpg")
Pil_Images = read_image(images)
main(images, Pil_Images, stores)