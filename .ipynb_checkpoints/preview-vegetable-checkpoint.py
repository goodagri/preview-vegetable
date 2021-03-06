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
    page_title='ηΎε ΄ηΆζ³',
    page_icon='π',
)


bucket_name = "vegi-upload-images"
s3 = boto3.resource('s3')
bucket = s3.Bucket('vegi-upload-images')

s3 = boto3.client('s3',
                  aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                  aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
                  region_name='ap-northeast-1'
                  )

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

    return blocks[1].text_input("γγΉγ―γΌγγε₯εγγ¦γγ γγ", help="γγγγε ΄εγ―okomeγ«θγγ¦γγ γγ", value="", type="password")

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
            st.error(f"ζ¬ζ₯γ?{store_name}γ?η»εγγγ¦γ³γ­γΌγγ§γγΎγγγ§γγ")

def clear_upload_images(stores):    
    latest_image_dict = get_latest_image_paths(stores, bucket_name=bucket_name)
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

def main(images, Pil_Images):
    """
    # πγγΈγγΈ
    ## ηΎε ΄ζζ°η»ει²θ¦§γ·γΉγγ 
    ____
    """    
    if st.button("ζζ°η»εγ«ζ΄ζ°"):
        state = st.empty()
        state.write("ζζ°γ?ε£²γε ΄η»εγ«ζ΄ζ°γγ¦γγΎγ....")
        clear_upload_images(stores)
        state.success("ζ΄ζ°ε?δΊ")

    for i, image in enumerate(images):
        st.markdown("## η«―ζ«οΌ"+image.split("/")[-1].split(".")[0].split("_")[0])
        time = images[i].split("/")[-1].split(".")[0].split("_")[1:]
        st.markdown("#### π·ζ?ε½±ζε»οΌ"+time[0]+"εΉ΄"+time[1][:2]+"ζ"+time[1][2:]+"ζ₯"+time[2][:2]+"ζ"+time[2][2:4]+"ε")
        st.image(Pil_Images[i], caption=images[i].split("/")[-1])
        st.markdown("___")

def setting_form():
    # Using the "with" syntax
    with st.form(key='my_form'):
        st.write("θ¨­ε?")
        total_device_list = get_device_list()
        if os.path.exists("./settings/device_settings.json"):
            with open("./settings/device_settings.json", "r") as f:
                watch_devices_dict = json.load(f)
            watch_devices_list = watch_devices_dict('devices')
        else:
            watch_device_list = total_device_list
        devices = st.multiselect(            
            "η«―ζ«γιΈγΆ",
            total_device_list,
            watch_device_list
        )
        submit_button = st.form_submit_button(label='θ¨­ε?ε€ζ΄')
    if submit_button:
        new_watch_devices_dict = {'devices': devices}
        with open("./settings/device_settings.json", "w") as f:
            json.dump(new_watch_devices_dict, f)



device_list = get_device_list()


login_blocks = generate_login_block()
password = login(login_blocks)

if is_authenticated(password):
    clean_blocks(login_blocks)
    images = glob("./latest_images/"+ "*.jpg")
    Pil_Images = read_image(images)
    setting_form()
    main(images, Pil_Images)

elif password:
    st.info("ζ­£γγγγΉγ―γΌγγε₯εγγ¦γγ γγ")


