import json
import os
from pyecharts.charts import Map, Tab
from pyecharts import options as opts
from collections import defaultdict

def load_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_data(data, key, is_percent=False):
    result = defaultdict(dict)
    for item in data:
        province = item.get("省份")
        level = item.get("酒店等级")
        val = item.get(key)
        if province and level and isinstance(val, (int, float)):
            result[(level, key)][province] = round(val * 100, 2) if is_percent else round(val, 2)
    return result

def create_map(title, data_dict):
    return (
        Map()
        .add(title, list(data_dict.items()), "china")
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_left="center",pos_top="10%"),
            visualmap_opts=opts.VisualMapOpts(
                min_=min(data_dict.values()),
                max_=max(data_dict.values()),
                is_piecewise=False,
                pos_top="center",
                pos_right="5%"
            )
        )
    )

def main():
    json_path = "results/price_change_by_province.json"
    output_dir = "heatmaps"
    os.makedirs(output_dir, exist_ok=True)

    data = load_data(json_path)

    # 分别构建三种类型的数据
    increase_data = build_data(data, "节中涨幅", is_percent=True)
    price_data = build_data(data, "节中", is_percent=False)
    fallback_data = build_data(data, "节后回落率", is_percent=True)

    tab = Tab(page_title="酒店热力图")

    # 合并所有数据
    combined_data = {}
    combined_data.update(increase_data)
    combined_data.update(price_data)
    combined_data.update(fallback_data)

    for (level, key), value_dict in combined_data.items():
        key_title = {
            "节中涨幅": "节中涨幅 (%)",
            "节中": "节中价格 (元)",
            "节后回落率": "节后回落率 (%)"
        }.get(key, key)

        title = f"{level}_{key_title}"
        map_chart = create_map(title, value_dict)
        tab.add(map_chart, title)

    output_file = os.path.join(output_dir, "country.html")
    tab.render(output_file)
    print(f"✅ 地图已生成并以 Tab 展示，文件路径：{output_file}")

if __name__ == "__main__":
    main()