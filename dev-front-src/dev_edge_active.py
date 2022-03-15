from cmath import log
from itertools import count
from operator import contains
import re
import streamlit as st
import os
import boto3
import glob
import datetime
import time
from boto3.dynamodb.conditions import Key, Attr
import pandas as pd
import cv2
import yaml
import json
import requests
import os
import pprint
import time
import urllib.error
from streamlit_folium import folium_static
import folium
import math
from dateutil import tz

@st.cache(ttl=10)
def cognito_auth(username, passwd):
    profile=os.environ.get("AWSPROFILE")
    userPoolId="ap-northeast-1_LtwNU2QXW"
    client_id="lm6paf1saf3nsqgfovvll90j8"
    try:
        my_session = boto3.Session(profile_name=profile)
        cognito_idp = my_session.client('cognito-idp')
        cognito_result = cognito_idp.admin_initiate_auth(
            UserPoolId = userPoolId,
            ClientId = client_id,
            AuthFlow = "ADMIN_USER_PASSWORD_AUTH",
            AuthParameters = {
                "USERNAME": username,
                "PASSWORD": passwd,
            }
        )
        response = cognito_idp.get_user(AccessToken=cognito_result["AuthenticationResult"]["AccessToken"])
        return response
    except Exception as e:
        print(e)
        return None

def generate_login_block():
    block1 = st.empty()
    block2 = st.empty()
    block3 = st.empty()
    block4 = st.empty()
    return block1, block2, block3, block4

def clean_blocks(blocks):
    for block in blocks:
        block.empty()

def login():
    block1 = st.empty()
    block2 = st.empty()
    block3 = st.empty()
    block4 = st.empty()
    block1.image("./fig/digivege.png")
    block2.header("ログインフォーム")    
    user = block3.text_input("ユーザ名を入力してください",value="")
    pw = block4.text_input("パスワードを入力してください", help="忘れた場合はグッド・アグリテクノロジーズ株式会社にお問い合わせください。\n(TEL：022-253-6410　e-mail：info@tech-goodagri.com)", value="", type="password")
    blocks = block1, block2, block3, block4
    return user, pw, blocks

# def get_store_id(gsi, table):
#     ready_stores = []
#     no_mail_stores = []
#     ready_response = table.query(IndexName=gsi,KeyConditionExpression=Key("status").eq("ready"))
#     ready_stores = [ready_response["Items"][i]["id"] for i in range(len(ready_response["Items"]))]
#     no_mail_response = table.query(IndexName=gsi,KeyConditionExpression=Key("status").eq("no_mail"))
#     no_mail_stores = [no_mail_response["Items"][i]["id"] for i in range(len(no_mail_response["Items"]))]
#     return ready_stores, no_mail_stores

def get_device_id(store_id, table):
    devices = []
    response = table.query(KeyConditionExpression=Key("id").eq(store_id) & Key("usage").eq("sensors"))
    devices = response["Items"][0]["sensors"]
    return devices

def get_info(store_id, table):
    response = table.query(KeyConditionExpression=Key("id").eq(store_id) & Key("usage").eq("web"))
    items = response["Items"][0]
    lat = items["lat"]
    long = items["long"]
    live_msg = items["live_msg"]
    return float(lat),float(long),str(live_msg)

def get_store_name(store_id, table):
    response = table.query(KeyConditionExpression=Key("id").eq(store_id) & Key("usage").eq("main"))
    items = response["Items"][0]
    store_name = items["store_name"]
    sensor_num = items["sensor_num"]
    return store_name, sensor_num

def get_image_name(store_ID, device_ID, s3, img_bucket, date_time, kind_of_image, clock):    
    prefix = store_ID + "/" + device_ID + date_time.strftime("/%Y/%m/%d/")
    response = s3.list_objects(Bucket=img_bucket, Prefix=prefix)
    if clock<10:
        check_time = date_time.strftime("%Y%m%d0") + str(int(clock))
    else:
        check_time = date_time.strftime("%Y%m%d") + str(int(clock))
    if kind_of_image == 1:
        JST = tz.gettz('Asia/Tokyo')
        for content in response["Contents"]:
            LastModified = content["LastModified"]
            LastModified = LastModified.astimezone(JST)
            LastModified_hour = LastModified.strftime("%Y%m%d%H")
            if LastModified_hour == check_time:
                latest_contents = content["Key"]
                break
            else:
                latest_contents = 0
    elif kind_of_image == 2:
        latest_contents = response["Contents"][0]["Key"]
    else:
        latest_contents = response["Contents"][-1]["Key"]
    save_time = latest_contents.split(".")[0]
    save_time = save_time.split("-")[-1]
    return latest_contents, save_time

def download_label(store_ID,device_ID,latest_contents, s3, outputs_bucket):    
    label_path = latest_contents.split(".")[0]
    label_name = label_path + ".txt"
    suffix = label_name.split("/")[-1]
    label_path_list = latest_contents.split("/")[:-2]
    prefix = "/".join(label_path_list)
    label = prefix + "/" + suffix
    try:
        local_path = "./" + store_ID + "/" + device_ID + ".txt"
        s3.download_file(outputs_bucket, label, local_path)
        label_flg = True
    except:
        label_flg = False
    return label_flg
        
def plot_bounding_boxes(img, store_id, device_id):
    label_name = "./" + store_id + "/" + device_id + ".txt"
    color = [(56,56,255),(151,157,255),(31,112,255),(29.178,255),(49,210,207),(10,249,72),(23,204,146),(134,219,61),(52,147,26),(187,212,0),(168,153,44),(255,194,0),(147,69,52),(255,115,100),(236,24,0),(255,56,132),(133,0,82),(255,56,203),(200,149,255),(199,55,255)]
    with open(label_name,"r") as file:
        data = file.readlines()
    dh, dw, _ = img.shape
    for dt in data:
        cls, x, y, w, h = dt.split(' ')
        nx = float(x)*dw
        ny = float(y)*dh
        nw = float(w)*dw
        nh = float(h)*dh
        x1 = int(nx-nw/2)
        y1 = int(ny-nw/2)
        x2 = int(nx+nw/2)
        y2 = int(ny+nh/2)
        color_num = int(cls) % int(len(color))
        cv2.rectangle(img, (x1,y1), (x2,y2), color[color_num], 4)
    return img

def browse_image(store_id, device_ID, path, s3, img_bucket):
    os.makedirs("./" +  store_id + "/device_images/", exist_ok=True)
    local_path = "./" +  store_id + "/device_images/" + device_ID + ".jpg"
    s3.download_file(img_bucket, path, local_path)

def get_csv_name(store_ID, s3, outputs_bucket, date_time):
    prefix = store_ID  + "/vegetable-data/" +  store_ID + date_time.strftime("-%Y-%m-%d")
    try:
        response = s3.list_objects(Bucket=outputs_bucket, Prefix=prefix)
        contents = response["Contents"][-1]["Key"]
    except:
        contents = ""
    return contents

def download_csv(store_id, path, s3, outputs_bucket):
    local_path = "./" +  store_id + "/data.csv"
    s3.download_file(outputs_bucket, path, local_path)

def get_date(dt):
    date_time = st.date_input("閲覧日時設定",min_value=datetime.date(2022, 1, 1),max_value=dt,value=dt)
    return date_time

def download_icon(url, dst_path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            with open(dst_path, mode='wb') as local_file:
                local_file.write(data)
    except urllib.error.URLError as e:
        print(e)

def get_wethear_data(store_id, lat,lon):
    with open(key_name,encoding="UTF-8") as file:
        obj = yaml.safe_load(file)
        key = obj["OW_API"] 
    url = "http://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&APPID={}".format(lat,lon,key)
    response = requests.get(url)
    data = response.json()
    icon = data["weather"][0]["icon"]
    temperature = round(float(data["main"]["temp"])-273.15,2)
    icon_url = 'http://openweathermap.org/img/wn/{}.png'.format(icon)
    dst_path = "./" +  store_id + '/weather.png'
    download_icon(icon_url, dst_path)
    return temperature

def clean_folder(store_id):
    image_list = glob.glob("./"+ store_id + "/device_images/*")
    if len(image_list)>0:
        for f in image_list:
            if os.path.isfile(f):
                 os.remove(f)
    csv_list = glob.glob("./" +  store_id + "/*.csv")
    if len(csv_list)>0:
        for f in csv_list:
            if os.path.isfile(f):
                 os.remove(f)

def prefix_determination(time_designation):
    if time_designation == "時刻指定":
        x = 1
    elif time_designation == "開店時":
        x = 2
    else:
        x = 3
    return x

def run(res):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("dev-digivege-store-table")
    s3 = boto3.client("s3")
    img_bucket = "vege-upload-images"
    outputs_bucket = "vege-outputs"
    gsi = "dev-digivege-store-status-gsi"
    # ready_stores, no_mail_stores = get_store_id(gsi,table)
    # stores = ready_stores + no_mail_stores
    today = datetime.date.today()
    #st.write(res)
    #st.write(res.get("UserAttributes"))
    user_info = res.get("UserAttributes")
    store_ids_info = [x for x in user_info if x['Name'] == 'custom:store_id'][0]
    store_ids_str = store_ids_info.get("Value")
    #st.write(store_ids_str.get("Value"))
    store_ids_list = store_ids_str.split("/")
    #st.write(store_ids_list)
    stores_info_list = []
    store_names_list = []
    for store in store_ids_list:
        #st.write(store)
        store_name, sensor_num = get_store_name(store, table)
        stores_info_dict = {"store_id":store, "store_name":store_name, "sensor_num":int(sensor_num)}
        stores_info_list.append(stores_info_dict)
        store_names_list.append(store_name)
    #st.write(stores_info_list)
    col00, col01 = st.columns([3,1])
    st.image("./fig/digivege.png")
    with st.sidebar:
        with st.form("form1"):
            selected_store_name = st.selectbox("店舗名",store_names_list)
            selected_store_info = [x for x in stores_info_list if x['store_name'] == selected_store_name][0]
            selected_sensor_num = selected_store_info.get("sensor_num")
            selected_store_id = selected_store_info.get("store_id")
            st.form_submit_button(label="更新")
    store_id = selected_store_id
    dir_name = "./" + store_id
    os.makedirs(dir_name, exist_ok=True) 
    sensor_num = int(selected_sensor_num)
    clock = 0
    with st.sidebar:
        with st.form("form2"):
            st.write("カメラ設置台数：{}台".format(sensor_num))
            date_time = get_date(today)
            time_designation = st.radio(label="",options=["最新売場状況","開店時","時刻指定"])
            if time_designation=="時刻指定":
                clock = st.number_input("24時間表記で入力してください",min_value=6,max_value=23,value=12,step=1)
            st.form_submit_button(label="更新")
    devices = get_device_id(store_id, table)
    kind_of_image = prefix_determination(time_designation)

    st.title("{}".format(store_name))
    output_date = date_time.strftime("%Y/%m/%d")
    output_time = time_designation
    if clock!=0:
        output_time = str(clock) + ":00"
    col002, col003 = st.columns(2)
    with col002:
        st.subheader("閲覧日時 : {}".format(output_date))
    with col003:
        st.subheader(output_time)
    try:
        clean_folder(store_id)
        #st.subheader("店舗画像")
        label_list = []
        for device_id in devices:
            try:
                latest_contents, save_time = get_image_name(store_id, device_id, s3, img_bucket, date_time, kind_of_image, clock)
                browse_image(store_id, device_id, latest_contents, s3, img_bucket)
                label_flg = download_label(store_id, device_id, latest_contents, s3, outputs_bucket)
                if label_flg:
                    label_list.append(device_id)
            except:
                d_name = device_id[-2:]
                st.write("※設定日時におけるカメラ{}の写真を取得できません。".format(str(int(d_name))))
        images = glob.glob("./" +  store_id + "/device_images/*")
        for image in images:
            D_name = os.path.basename(image).split(".")[0]
            output_name = "📷カメラ" + str(int(D_name[-2:]))
            img = cv2.imread(image)
            st.subheader(output_name)
            if D_name in label_list:
                plot_bb = st.checkbox("デジベジAI", key=D_name)
                if plot_bb:
                    img = plot_bounding_boxes(img, store_id, D_name)
            img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            st.image(img, caption="撮影時刻：{}：{}".format(save_time[:2],save_time[2:]))
    except:
        st.text("選択した日付の写真はありません。")
    try:
        st.subheader("野菜の動き")
        csv_name = get_csv_name(store_id, s3, outputs_bucket, date_time)
        download_csv(store_id, csv_name, s3, outputs_bucket)
        file_neme = "./" + store_id + "/data.csv"
        df = pd.read_csv(file_neme, encoding="UTF-8")
        df["index"] =  pd.to_datetime(df["index"],format="%Y-%m-%d %H:%M:%f")
        df = df.set_index("index")
        df = df.rolling(5).mean()
        df = df.dropna(how="all",axis=0)
        total_vege = df.columns
        with st.sidebar:
            with st.form("form3"): 
                selested_list_data = st.multiselect("表示する野菜", total_vege.to_list(), total_vege.to_list())
                st.form_submit_button(label="更新")
        y = selested_list_data
        st.line_chart(df[selested_list_data])
    except:
        st.text("選択した日付のデータはありません。")
    
    try:
        lat, longi, live_msg = get_info(store_id,table)
        date_judge = live_msg.split("\\")[0]
        date_judge = date_judge.split("　")[-1]
        date_judge = date_judge[:2] + date_judge[3:5]
        date_now = datetime.datetime.now()
        date_now = date_now.strftime("%m%d")
        live_msg = live_msg.replace('\u3000', '　').replace("\\","").replace('n', '\n')
        st.markdown("---")
        temperature = get_wethear_data(store_id, lat,longi)
        data = {"lat":lat,"lon":longi}
        #map_data = pd.DataFrame(data,index=[map])
        col3, col4 = st.columns([3,1])
        with col3:
            st.subheader("最新の店舗状況")
            if date_judge==date_now:
                st.text(live_msg)
            else:
                st.text("おはようございます。\n最新の売り場状況は写真よりご確認ください。\n皆様のご出荷を心よりお待ちしております。")
        with col4:
            st.subheader("現在の天気")
            weather_image = "./" + store_id + "/weather.png"
            st.image(weather_image)
            st.text("気温\n{}℃".format(temperature))
        # st.subheader("店舗位置情報")
        # #st.map(map_data)
        # m = folium.Map(location=[lat,longi], zoom_start=15)
        # folium.Circle(radius=1000,location=[lat,longi],popup=[store_name],color="blue",fill=True,fill_opacity=0.07).add_to(m)
        
        # folium_static(m)
    except:
        st.text("選択した日付のメッセージはありません。\nまたは位置情報が登録されていません。")
    
    st.markdown("---")
    st.subheader("お問い合わせ")
    col5, col6 = st.columns([2,1])
    with col5:
        st.text("当サービスをご利用いただきありがとうございます。\nご意見ご要望、不具合等ございましたら下記までご連絡ください。\n\nグッド・アグリテクノロジーズ株式会社\nTEL：022-253-6410\ne-mail：info@tech-goodagri.com\n")
    with col6:
        st.image("./fig/robot4.png")

key_name = "./key.yaml"
st.set_page_config(page_title = "デジベジ稼働確認画面", page_icon = "🥕")    

if "login" not in st.session_state:
    user_id,password, blocks = login()
    block = st.empty()
    login_button = block.button("ログイン")
    if login_button:
        res = cognito_auth(user_id, password)
        if res is not None:
            block.empty()
            clean_blocks(blocks)
            st.session_state["login"] = res                        
        else:
            st.info("正しいパスワードを入力してください")

if "login" in st.session_state:
    run(st.session_state["login"])