from pypinyin import lazy_pinyin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import os

def city_to_english(city_name):
    pinyin = lazy_pinyin(city_name)
    return ''.join(word.capitalize() for word in pinyin)

def crawler():
    # 设置无头浏览器
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)

    # 设置参数
    cities = ["石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水",
              "太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁",
              "呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布",
              "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛",
              "长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城",
              "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化",
              "南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁",
              "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水",
              "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城",
              "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德",
              "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶",
              "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽",
              "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店",
              "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州",
              "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底",
              "广州", "韶关", "深圳", "珠海", "汕头", "佛山", "江门", "湛江", "茂名", "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮",
              "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左",
              "海口", "三亚", "三沙", "儋州",
              "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳",
              "贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁",
              "昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧",
              "拉萨", "日喀则", "昌都", "林芝", "山南", "那曲",
              "西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛",
              "兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南",
              "西宁", "海东",
              "银川", "石嘴山", "吴忠", "固原", "中卫",
              "乌鲁木齐", "克拉玛依", "吐鲁番", "哈密",
              "北京","上海","天津","重庆"]
    dates = ["2025-05-29", "2025-05-30", "2025-05-31", "2025-06-01", "2025-06-02", "2025-06-03", "2025-06-04"]
    for city in cities:
        results = []
        print(f"city：{city_to_english(city)}")
        base_url = f"https://hrewards.huazhu.com/hotel?cityName={city}&checkInDate=2025-05-29&checkOutDate=2025-05-30&keyword="

        # 打开第一页
        driver.get(base_url + "&pageIndex=1")
        time.sleep(4)

        # 获取最大页码数
        page_elements = driver.find_elements(By.CSS_SELECTOR, ".hzrc-item a[rel='nofollow']")
        page_numbers = []
        for el in page_elements:
            try:
                num = int(el.text)
                page_numbers.append(num)
            except:
                continue
        max_page = max(page_numbers) if page_numbers else 1
        print(f"total pages: {max_page} ")
        for date in dates:
            checkin = date
            checkout = pd.to_datetime(date) + pd.Timedelta(days=1)
            checkout = checkout.strftime("%Y-%m-%d")
            for page in range(1, max_page + 1):
                print(f"city:{city_to_english(city)}, page: {page}, checkin: {checkin}, checkout: {checkout}")
                url = f"https://hrewards.huazhu.com/hotel?cityName={city}&checkInDate={checkin}&checkOutDate={checkout}&keyword=&pageIndex={page}"
                driver.get(url)
                time.sleep(4)

                # 抓取酒店数据
                hotels = driver.find_elements(By.CLASS_NAME, "borderE0")

                for hotel in hotels:
                    try:
                        name = hotel.find_element(By.CLASS_NAME, "hotel-name").text
                        location = hotel.find_element(By.CLASS_NAME, "hotel-loc").text
                        price_now = hotel.find_element(By.CSS_SELECTOR, ".hotel-price .price .bold").text.replace("￥","").strip()
                        price_origin = hotel.find_element(By.CSS_SELECTOR, ".hotel-price .market span").text.replace("￥","").strip()
                        hotel_star = hotel.find_element(By.CLASS_NAME, "hotel-star")
                        hotel_type = hotel_star.find_elements(By.CLASS_NAME, "line")[-1].text

                        results.append({
                            "城市": city,
                            "日期": checkin,
                            "酒店名称": name,
                            "位置": location,
                            "优惠价": price_now,
                            "门市价": price_origin,
                            "酒店等级": hotel_type
                        })
                    except Exception as e:
                        continue

        # 保存数据
        df = pd.DataFrame(results)
        df.to_csv(f"hotels2/{city_to_english(city)}.csv", index=False, encoding="utf-8-sig")
    driver.quit()
    print("Done!")

def main():
    os.makedirs("hotels", exist_ok=True)
    crawler()
if __name__ == '__main__':
    main()