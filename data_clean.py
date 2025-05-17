from fileinput import filename

import pandas as pd
import os

def clean_hotel_data():
    os.makedirs("cleaned", exist_ok=True)
    files = [f for f in os.listdir("txt") if f.endswith(".txt")]
    output_file = "cleaned/cleaned_hotels.txt"
    log_file = "cleaned/clean_log.txt"
    all_data = []
    with open(log_file, "w", encoding="utf-8") as log:
        for file in files:
            # 读取 TXT 文件（制表符分隔）
            df = pd.read_csv("txt/"+file, sep='\t', dtype=str)
            df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)
            print(f"start: {file}")
            # 转换“优惠价”为数字类型（有非法字符的转为 NaN）
            df["优惠价"] = pd.to_numeric(df["优惠价"], errors="coerce")

            # 去除以下缺失值的记录
            df_cleaned = df.dropna(subset=["优惠价", "酒店等级"])
            # 去除地理编码错误酒店
            df_cleaned = df_cleaned[df_cleaned.apply(lambda x: str(x["城市"]) in str(x["标准城市"]), axis=1)]
            # 对每家酒店保留日期数 == 7 的
            df_cleaned["日期"] = pd.to_datetime(df_cleaned["日期"], errors="coerce")  # 确保日期格式正确
            df_cleaned = df_cleaned.dropna(subset=["日期"])  # 删除无效日期

            hotel_valid = (
                df_cleaned.groupby(["城市", "酒店名称"])["日期"]
                .nunique()
                .reset_index(name="天数")
            )
            hotel_valid = hotel_valid[hotel_valid["天数"] == 7]

            df_cleaned = df_cleaned.merge(hotel_valid[["城市", "酒店名称"]], on=["城市", "酒店名称"], how="inner")
            # 去除区县缺失值的记录
            df_cleaned = df_cleaned.loc[(df_cleaned["区县"].notna()) & (df_cleaned["区县"].astype(str) != "[]")]
            all_data.append(df_cleaned)
            filename=file.replace('_','')
            log_line = f"clean：{filename}，total：{len(df_cleaned)}"
            print(log_line)
            log.write(log_line + "\n")

    # 保存清洗后的数据
    merged_df = pd.concat(all_data, ignore_index=True)
    merged_df.to_csv(output_file, sep='\t', index=False)


# 示例调用
if __name__ == "__main__":
        clean_hotel_data()