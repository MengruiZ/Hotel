import requests
import pandas as pd
import time
from pypinyin import lazy_pinyin
import os
import re
def is_effectively_empty(csv_path):
    # 如果文件不存在或大小为 0，直接认为是空的
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        print(f"跳过空文件: {csv_path}")
        return True

    # 打开文件看是否全是空白字符
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 去除可能的 BOM 字符（\ufeff）
        cleaned = content.replace('\ufeff', '').strip()
        if cleaned == "":
            print(f"跳过空文件: {csv_path}")
            return True
    return False
def process_csv_to_txt(input_csv):
    if is_effectively_empty(input_csv):
        return None
    # 读取CSV
    df = pd.read_csv(input_csv)
    if df.empty or df.shape[1] == 0:
        return  None
    # 创建新的列：省份，城市，区县
    provinces = []
    formatted_address = []
    districts = []
    formatted_city = []
    # 建立缓存，避免重复调用 API
    cache = {}

    for i, row in df.iterrows():
        location = row['位置']
        map={}
        if location in cache:
            map = cache[location]
        else:
            city = row['城市']
            location = row['位置']
            hotel=row['酒店名称']
            map = geocode_amap(city,location,hotel)
            cache[location] = map
            time.sleep(0.2)  # 防止频繁请求被限速
        if map is not None:
            formatted_address.append(map["formatted_address"])
            provinces.append(map["province"])
            districts.append(map["district"])
            formatted_city.append(map["city"])
        else:
            formatted_address.append("")
            provinces.append("")
            districts.append("")
            formatted_city.append("")
    # 添加新列
    df['省份'] = provinces
    df['标准城市'] = formatted_city
    df['区县'] = districts
    df['格式化地址'] = formatted_address

    # 写入 txt，列之间用 \t 分隔
    output_txt='txt2/'+city_to_english(city)+'.txt'
    df.to_csv( output_txt,sep='\t', index=False)

    print(f" 处理完成，已保存为：{output_txt}")

def remove_parentheses(text):
    return re.sub(r"[（(][^）)]+[）)]", "", text)
def city_to_english(city_name):
    pinyin = lazy_pinyin(city_name)
    return '_'.join(word.capitalize() for word in pinyin)

def geocode_amap(city, location, hotel):
    AMAP_URL = 'https://restapi.amap.com/v3/geocode/geo?parameters'
    AMAP_KEY1='231e3d7e3c41da3661420d5b5f100287'
    AMAP_KEY2='9f56af70d33b219431c4e41284f2b438'
    clean_loc = remove_parentheses(location)
    address_candidates = [
        f"{city}市{location}{hotel}",
        f"{city}市{hotel}",
        f"{city}市{location}",
    ]
    if clean_loc != location:  # 只有 location 含括号时才增加额外尝试
        address_candidates.extend([
            f"{city}市{clean_loc}",
            f"{city}市{clean_loc}{hotel}",
        ])

    for addr in address_candidates:
        for key in (AMAP_KEY1, AMAP_KEY2):  # 先尝试 KEY2，失败后用 KEY1
            params = {"address": addr, "key": key}
            try:
                resp = requests.get(AMAP_URL, params=params, timeout=5).json()
            except Exception as e:
                print(f"请求失败 {addr}: {e}")
                time.sleep(0.5)
                continue

            print(f"尝试地址: {addr} 使用Key: {key[-4:]} -> 返回: {resp}")

            status = resp.get("status")
            info_code = resp.get("infocode", "")

            if status == "1" and resp.get("count") != "0":
                r = resp["geocodes"][0]
                return {
                    "formatted_address": r.get("formatted_address"),
                    "province": r.get("province"),
                    "city": r.get("city"),
                    "district": r.get("district"),
                }

            # 如果是状态码开头为10044的错误，尝试另一个 key
            if info_code.startswith("10044"):
                print(f"Key 失效或配额限制，切换 Key：{key[-4:]}")
                continue  # 切换到下一个 key 尝试

            # 如果不是 key 的问题，退出 key 尝试，尝试下一个地址
            break

            # 每个地址尝试后稍作延迟
        time.sleep(0.5)

    # 所有尝试都失败
    print(f"无法定位: {city}市{location}{hotel}")
    return None
def read_csvs_in_order(folder_path):
    # 获取所有CSV文件（过滤非CSV）
    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

    # 按文件名排序（字母顺序/数字顺序）
    files.sort()

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        process_csv_to_txt(file_path)
        # is_effectively_empty(file_path)
if __name__ == '__main__':
    os.makedirs("txt", exist_ok=True)
    read_csvs_in_order("hotels")