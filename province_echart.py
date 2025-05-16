import json
from collections import defaultdict
from pyecharts import options as opts
from pyecharts.charts import Map, Tab

# 加载 JSON 数据
with open("results/impact_by_hotel_type.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 数据结构：省份 -> 酒店等级 -> 城市数据列表
province_hoteltype_data = defaultdict(lambda: defaultdict(list))

for d in data:
    if all(k in d for k in ["省份", "城市", "酒店等级", "节中", "节中涨幅", "节后回落率"]):
        province = d["省份"]
        city = d["城市"]
        level = d["酒店等级"]
        province_hoteltype_data[province][level].append({
            "city": city,
            "节中": round(d["节中"], 2),
            "节中涨幅": round(d["节中涨幅"] * 100, 2),  # 百分比
            "节后回落率": round(d["节后回落率"] * 100, 2),  # 百分比
        })

# 通用地图绘制函数
def draw_map(province_name, data_list, value_key, title):
    return (
        Map()
        .add(
            series_name=title,
            data_pair=[(item["city"], item[value_key]) for item in data_list],
            maptype=province_name,
            is_map_symbol_show=False
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            visualmap_opts=opts.VisualMapOpts(
                min_=min(item[value_key] for item in data_list),
                max_=max(item[value_key] for item in data_list),
                is_piecewise=False,
                pos_left="left"
            )
        )
    )

# 创建总 Tab 页面（每张图一个 Tab）
tab = Tab()

# 遍历每个省份、酒店等级和图表类型
for province, level_data in province_hoteltype_data.items():
    safe_province = province.replace("省", "").replace("市", "").replace("自治区", "")

    for hotel_level, cities in level_data.items():
        indicators = [("节中涨幅", "节中价格涨幅 (%)"),
                      ("节后回落率", "节后回落率 (%)"),
                      ("节中", "节中价格 (元)")]

        for value_key, label in indicators:
            chart_title = f"{province} - {hotel_level}：{label}"
            tab_title = f"{safe_province}-{hotel_level}-{label}"
            chart = draw_map(safe_province, cities, value_key, chart_title)
            tab.add(chart, tab_title)

# 输出到一个 HTML 文件
output_file = "hoteltype_maps_by_indicator.html"
tab.render(output_file)
print(f"✅ 每张图已作为独立页签输出到 {output_file}")