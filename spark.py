from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, stddev, max, min, when, round, row_number
from pyspark.sql.window import Window
import os
import json

# 初始化 SparkSession
spark = SparkSession.builder.appName("Festival Hotel Price Ranking").getOrCreate()

def write_json(df, path):
    data = df.toPandas().to_dict(orient="records")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 价格均值 + 涨幅分析
def analyze_price_change(df, group_cols, name_prefix, out_path):
    avg_by_stage = df.groupBy(*group_cols, "date_type") \
        .agg(round(avg("优惠价"), 2).alias("avg_price"))

    pivot = avg_by_stage.groupBy(*group_cols).pivot("date_type", ["节前", "节中", "节后"]) \
        .agg(avg("avg_price")) \
        .withColumn("节中涨幅", round((col("节中") - col("节前")) / col("节前"), 4)) \
        .withColumn("节后回落率", round((col("节后") - col("节前")) / col("节前"), 4))

    write_json(pivot, f"{out_path}/{name_prefix}_price_change.json")
    return pivot

# 价格波动分析
def analyze_volatility(df, group_cols, name_prefix, out_path):
    volatility = df.groupBy(*group_cols) \
        .agg(
            round(stddev("优惠价"), 2).alias("标准差"),
            round((max("优惠价") - min("优惠价")), 2).alias("极差")
        )
    write_json(volatility, f"{out_path}/{name_prefix}_volatility.json")
    return volatility

# 排名前 N 的单位
def rank_top_n(df, group_keys, rank_by, n, name_prefix, out_path):
    # 对每个酒店等级单独排序
    window_spec = Window.partitionBy("酒店等级").orderBy(col(rank_by).desc())
    ranked_df = df.withColumn("rank", row_number().over(window_spec)).filter(col("rank") <= n)
    ranked_df = ranked_df.drop("rank")
    write_json(ranked_df, f"{out_path}/{name_prefix}_top_{rank_by}.json")

# 主函数
def main():
    input_file = "hdfs:///home/mengrui_zhang/hotel/HotelData/cleaned_hotels.txt"
    out_path = "results"
    os.makedirs(out_path, exist_ok=True)

    df = spark.read.option("delimiter", "\t").option("header", True).csv(input_file)

    df = df.withColumn("优惠价", col("优惠价").cast("double")) \
        .withColumn("日期", col("日期").cast("date")) \
        .withColumn(
            "date_type",
            when(col("日期") < "2025-05-31", "节前")
            .when(col("日期") > "2025-06-02", "节后")
            .otherwise("节中")
        )

    ## 各级别行政区划：省、市、区县
    levels = [
        (["省份", "酒店等级"], "province"),
        (["省份", "城市","标准城市", "酒店等级"], "city"),
        (["省份", "城市","标准城市", "区县", "酒店等级"], "district")
    ]

    for group_cols, prefix in levels:
        price_df = analyze_price_change(df, group_cols, f"{prefix}_type", out_path)
        vol_df = analyze_volatility(df, group_cols, f"{prefix}_type", out_path)

        # 排名：节中价格、节中涨幅、节后回落率、标准差
        rank_top_n(price_df, group_cols, "节中", 10, f"{prefix}_type", out_path)
        rank_top_n(price_df, group_cols, "节中涨幅", 10, f"{prefix}_type", out_path)
        rank_top_n(price_df, group_cols, "节后回落率", 10, f"{prefix}_type", out_path)
        rank_top_n(vol_df, group_cols, "标准差", 10, f"{prefix}_type", out_path)

    print("排名分析完成：各级别排名结果输出成功。")

if __name__ == "__main__":
    main()