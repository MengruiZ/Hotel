import pandas as pd
import os

def clean_hotel_data():
    os.makedirs("cleaned", exist_ok=True)
    files = [f for f in os.listdir("txt") if f.endswith(".txt")]
    output_file = "cleaned/cleaned_hotels.txt"
    all_data = []
    for file in files:
        # 读取 TSV 文件（制表符分隔）
        df = pd.read_csv("txt/"+file, sep='\t', dtype=str)

        # 转换“优惠价”为数字类型（有非法字符的转为 NaN）
        df["优惠价"] = pd.to_numeric(df["优惠价"], errors="coerce")

        # 去除以下缺失值的记录
        df_cleaned = df.dropna(subset=["区县", "优惠价", "酒店等级"])
        # 对每家酒店保留日期数 >= 7 的
        df_cleaned["日期"] = pd.to_datetime(df_cleaned["日期"], errors="coerce")  # 确保日期格式正确
        df_cleaned = df_cleaned.dropna(subset=["日期"])  # 删除无效日期

        hotel_valid = (
            df_cleaned.groupby("酒店名称")["日期"]
            .nunique()
            .reset_index(name="天数")
        )
        hotel_valid = hotel_valid[hotel_valid["天数"] >= 7]

        df_cleaned = df_cleaned[df_cleaned["酒店名称"].isin(hotel_valid["酒店名称"])]

        all_data.append(df_cleaned)
        print(f"已清洗完成：{output_file}，剩余记录数：{len(df_cleaned)}")

    # 保存清洗后的数据
    merged_df = pd.concat(all_data, ignore_index=True)
    merged_df.to_csv(output_file, sep='\t', index=False)


# 示例调用
if __name__ == "__main__":
        clean_hotel_data()