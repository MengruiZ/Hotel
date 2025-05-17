import re
import json
import os
from collections import defaultdict
from pyecharts.charts import Map, Bar, Page
from pyecharts import options as opts

# === 配置 ===
base_path = "results"       # 原始 JSON 数据目录
output_dir = "output"        # 所有 HTML 输出统一目录
os.makedirs(output_dir, exist_ok=True)

# === 公共函数 ===
def generate_index(index_file="index.html"):
    from collections import defaultdict

    index_data = {
        "省级": defaultdict(list),
        "市级": defaultdict(lambda: defaultdict(list)),
        "区级": defaultdict(lambda: defaultdict(list)),
        "Top10": defaultdict(list),
    }

    # 收集 output 文件
    for filename in os.listdir("output"):
        if not filename.endswith(".html"):
            continue
        filepath = os.path.join("output", filename)
        if filename.startswith("省级_"):
            parts = filename.replace(".html", "").split("_")
            hotel = parts[1]
            metric = parts[2]
            index_data["省级"][hotel].append((metric, filepath))
        elif filename.startswith("市级_"):
            parts = filename.replace(".html", "").split("_")
            province = parts[1]
            hotel = parts[2]
            metric = parts[3]
            index_data["市级"][province][hotel].append((metric, filepath))
        elif filename.startswith("区级_"):
            parts = filename.replace(".html", "").split("_")
            city = parts[1]
            hotel = parts[2]
            metric = parts[3]
            index_data["区级"][city][hotel].append((metric, filepath))

    # 收集 top10 文件
    if os.path.exists("output"):
        for filename in os.listdir("output"):
            if filename.endswith(".html"):
                filepath = os.path.join("output", filename)
                if "top10" in filename:
                    # 通过文件名判断指标
                    if "节中" in filename:
                        metric = "节中均价"
                    elif "节中涨幅" in filename:
                        metric = "节中涨幅"
                    elif "节后回落率" in filename:
                        metric = "节后回落率"
                    elif "标准差" in filename:
                        metric = "价格波动"
                    else:
                        metric = filename
                    index_data["Top10"]["所有酒店等级"].append((metric, filepath))

    # 生成 HTML
    html = [
        "<html><head><meta charset='utf-8'><title>图表索引</title></head><body>",
        "<h1>图表索引</h1>"
    ]

    def render_collapsible(group_dict, level_name):
        html.append(f"<details open><summary>{level_name}</summary>")
        for k1, v1 in sorted(group_dict.items()):
            html.append(f"<details><summary>{k1}</summary>")
            if isinstance(v1, dict):
                for k2, v2 in sorted(v1.items()):
                    html.append(f"<details><summary>{k2}</summary><ul>")
                    for metric, path in sorted(v2):
                        html.append(f"<li><a href='{path}' target='_blank'>{metric}</a></li>")
                    html.append("</ul></details>")
            else:
                html.append("<ul>")
                for metric, path in sorted(v1):
                    html.append(f"<li><a href='{path}' target='_blank'>{metric}</a></li>")
                html.append("</ul>")
            html.append("</details>")
        html.append("</details>")

    render_collapsible(index_data["省级"], "省级")
    render_collapsible(index_data["市级"], "市级")
    render_collapsible(index_data["区级"], "区级")
    render_collapsible(index_data["Top10"], "Top10 图表")

    html.append("</body></html>")

    with open(index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"折叠式索引页面已生成: {index_file}")

def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_province_name(province):
    if not province:
        return ""
    return re.sub(r"(省|市|自治区|回族自治区|维吾尔自治区|壮族自治区|藏族自治区)$", "", province)

def safe_name(s):
    return re.sub(r"[^\w\u4e00-\u9fff]+", "_", s)

# === 热力图绘制 ===

def create_heatmap(data, value_key, title, level_name, maptype):
    datalist = []
    for item in data:
        if item.get(value_key) is not None and item.get(level_name):
            datalist.append((item[level_name], item[value_key]))

    if not datalist:
        return None

    return (
        Map()
        .add(
            series_name=value_key,
            data_pair=datalist,
            maptype=maptype,
            is_map_symbol_show=False,
            name_map=None
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            visualmap_opts=opts.VisualMapOpts(max_=max(v for _, v in datalist)),
        )
    )

def render_province(json_file):
    data = read_json(os.path.join(base_path, json_file))
    metrics = ["节中涨幅", "节后回落率", "标准差"]
    hotel_types = set(d["酒店等级"] for d in data if "酒店等级" in d)

    for hotel in hotel_types:
        for metric in metrics:
            filtered = [d for d in data if d.get("酒店等级") == hotel]
            chart = create_heatmap(filtered, metric, f"省级 - {hotel} - {metric}", "省份", "china")
            if chart:
                page = Page()
                page.add(chart)
                filename = f"省级_{safe_name(hotel)}_{metric}.html"
                page.render(os.path.join(output_dir, filename))

def render_city(json_file):
    data = read_json(os.path.join(base_path, json_file))
    metrics = ["节中涨幅", "节后回落率", "标准差"]
    grouped = defaultdict(lambda: defaultdict(list))

    for d in data:
        prov = d.get("省份")
        hotel = d.get("酒店等级")
        if prov and hotel:
            grouped[prov][hotel].append(d)

    for prov, hotel_map in grouped.items():
        prov_clean = clean_province_name(prov)
        for hotel, records in hotel_map.items():
            for metric in metrics:
                filtered = [d for d in records if d.get(metric) is not None]
                chart = create_heatmap(filtered, metric, f"市级 - {prov} - {hotel} - {metric}", "标准城市", prov_clean)
                if chart:
                    page = Page()
                    page.add(chart)
                    filename = f"市级_{safe_name(prov)}_{safe_name(hotel)}_{metric}.html"
                    page.render(os.path.join(output_dir, filename))

def render_district(json_file):
    data = read_json(os.path.join(base_path, json_file))
    metrics = ["节中涨幅", "节后回落率", "标准差"]
    grouped = defaultdict(lambda: defaultdict(list))

    for d in data:
        city = d.get("城市")
        hotel = d.get("酒店等级")
        if city and hotel:
            grouped[city][hotel].append(d)

    for city, hotel_map in grouped.items():
        for hotel, records in hotel_map.items():
            for metric in metrics:
                filtered = [d for d in records if d.get(metric) is not None]
                chart = create_heatmap(filtered, metric, f"区级 - {city} - {hotel} - {metric}", "区县", city)
                if chart:
                    page = Page()
                    page.add(chart)
                    filename = f"区级_{safe_name(city)}_{safe_name(hotel)}_{metric}.html"
                    page.render(os.path.join(output_dir, filename))

# === 柱状图绘制（Top10）===

def create_bar(data, title, value_key, level_name):
    bar = Bar()
    names = [f"{item.get('省份', '')}-{item.get('城市', '')}-{item.get('区县', '')}".strip("-") for item in data]
    values = [item.get(value_key, 0) for item in data]

    bar.add_xaxis(names)
    bar.add_yaxis(title, values)
    bar.set_global_opts(
        title_opts=opts.TitleOpts(title=f"{title} - {level_name}"),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
        datazoom_opts=[opts.DataZoomOpts()],
        toolbox_opts=opts.ToolboxOpts()
    )
    return bar

def generate_chart_html(value_key, chart_title):
    levels = {
        "province": "省份",
        "city": "城市",
        "district": "区县"
    }

    page = Page(layout=Page.SimplePageLayout)

    for level_key, level_name in levels.items():
        path = os.path.join(base_path, f"{level_key}_type_top_{value_key}.json")
        if not os.path.exists(path):
            print(f"文件不存在: {path}")
            continue

        data = read_json(path)
        level_group = defaultdict(list)
        for row in data:
            htype = row.get("酒店等级", "未知")
            level_group[htype].append(row)

        for hotel_type, items in level_group.items():
            title = f"{chart_title}（{hotel_type}）"
            bar = create_bar(items, title, value_key, level_name)
            page.add(bar)

    output_file = os.path.join(output_dir, f"{value_key}_top10.html")
    page.render(output_file)
    print(f"图表已保存为: {output_file}")

# === 主函数 ===

def main():
    # 热力图输出
    render_province("province_type_price_change.json")
    render_province("province_type_volatility.json")

    render_city("city_type_price_change.json")
    render_city("city_type_volatility.json")

    render_district("district_type_price_change.json")
    render_district("district_type_volatility.json")

    # 柱状图 Top10 输出
    generate_chart_html("节中", "节中均价 Top10")
    generate_chart_html("节中涨幅", "节中涨幅 Top10")
    generate_chart_html("节后回落率", "节后回落率 Top10")
    generate_chart_html("标准差", "价格波动 Top10")

if __name__ == "__main__":
    main()
    generate_index()