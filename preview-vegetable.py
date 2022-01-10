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
# AE01-Wb5qCH
"""



bucket_name = "vege-upload-images"
s3 = boto3.resource('s3')
bucket = s3.Bucket('vege-upload-images')

dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('dev-digivege-store-table')

s3 = boto3.client('s3',
                  aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                  aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
                  region_name='ap-northeast-1'
                  )

store_name = "AE01-Wb5qCH"

def is_authenticated(password):
    return password == st.secrets["PRE_PASSWORD"]

def generate_login_block():
    block1 = st.empty()
    block2 = st.empty()

    return block1, block2

def clean_blocks(blocks):
    for block in blocks:
        block.empty()

def login(blocks):
    blocks[0].markdown("""
            <style>
                input {
                    -webkit-text-security: disc;
                }
            </style>
        """, unsafe_allow_html=True)

    return blocks[1].text_input("パスワードを入力してください", help="わすれた場合はokomeに聞いてください", value="", type="password")

def latest_image_path(store_name, device_name, bucket_name, dt):
    prefix = store_name +"/"+ device_name + dt.strftime("/%Y/%m/%d/")
    st.write(prefix)
    response = s3.list_objects(Bucket=bucket_name, Prefix=prefix)
    if "Contents" in response:
        contents = response["Contents"][-1]
        return contents["Key"]
    else:
        return 0
        
def get_latest_image_paths(devices, bucket_name, dt):
    latest_image_dict = {}
    for device in devices:
        latest_image = latest_image_path(store_name, device, bucket_name, dt)
        latest_image_dict[device] = latest_image
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

def clear_upload_images(devices, dt):    
    latest_image_dict = get_latest_image_paths(devices, bucket_name=bucket_name, dt=dt)
    download_image(latest_image_dict)

@st.cache
def read_image(images):
    pil_imgs = []
    for i, image in enumerate(images):
        pil_img = Image.open(image)
        pil_imgs.append(pil_img)
    return pil_imgs

@st.cache
def get_device_list(store_name):
    device_list = table.get_item(Key={"id": store_name, "usage": "sensors"})["Item"]["sensors"]
    return device_list

def display_images(images):
    for i, image in enumerate(images):
        time = images[i].split("/")[-1].split(".")[0].split("-")
        st.markdown("## 端末："+time[2])
        st.markdown("#### 📷撮影時刻："+time[3]+"年"+time[4][:2]+"月"+time[4][2:]+"日"+time[5][:2]+"時"+time[5][2:]+"分")
        st.image(Pil_Images[i], caption=images[i].split("/")[-1])
        st.markdown("___")

def main(images, Pil_Images, devices, dt):
    if st.button("最新画像に更新"):
        state = st.empty()
        state.write("最新の売り場画像に更新しています....")
        clear_upload_images(devices, dt)
        state.success("更新完了")

    display_images(images)

def setting_form():
    # Using the "with" syntax
    with st.form(key='my_form'):
        st.write("設定")
        total_device_list = get_device_list(store_name)
        if os.path.exists("./settings/device_settings.json"):
            with open("./settings/device_settings.json", "r") as f:
                watch_devices_dict = json.load(f)
            watch_device_list = watch_devices_dict['devices']
        else:
            watch_device_list = total_device_list
        devices = st.multiselect(            
            "端末",
            total_device_list,
            watch_device_list
        )
        dt = st.date_input(
            "日時",
            datetime.datetime.now())
        submit_button = st.form_submit_button(label='設定変更')
    if submit_button:
        new_watch_devices_dict = {'devices': devices}
        if not os.path.exists('settings'):
            os.mkdir('settings')
        with open("./settings/device_settings.json", "w") as f:
            json.dump(new_watch_devices_dict, f)
    return devices ,dt



login_blocks = generate_login_block()
password = login(login_blocks)

# if is_authenticated(password):
if True:
    """
    # 🍅デジベジ
    ## 現場最新画像閲覧システム
    ____
    """    
    clean_blocks(login_blocks)
    images = glob("./latest_images/"+ "*.jpg")
    Pil_Images = read_image(images)
    devices,dt = setting_form()
    main(images, Pil_Images, devices, dt)

elif password:
    st.info("正しいパスワードを入力してください")


