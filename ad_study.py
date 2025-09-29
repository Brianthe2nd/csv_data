import pandas as pd
from gemini import get_levels,clean_ai_response
from utils import get_frame
import uuid
import cv2
import os
import json
import traceback
import time
import subprocess

df = pd.read_csv("backtest_results.csv")

def shutdown():
    subprocess.run(["sudo", "shutdown", "-h", "now"], check=False)

mask = df["filename"].isna() | (df["filename"].astype(str).str.strip().str.lower().isin(["", "nan"]))
df_to_process = df[mask]

for idx, row in df_to_process.iterrows():
    try:
        val = row["filename"]

        # only process rows where filename is missing
        if not (pd.isna(val) or str(val).lower() == "nan" or val == ""):
            print("File name is:", val)
            continue  # skip this row, already has filename

        # --- your processing logic here ---
        time.sleep(5)
        trade_type = row["trade_action"]
        sl = row["sl"]
        tp = row["tp"]
        status = row["status"]

        trade_data = {"trade_type": trade_type, "status": status, "sl": sl, "tp": tp}

        image = get_frame(row["link"], cookies_file="b159.txt")
        filename = f"{uuid.uuid4().hex}"
        os.makedirs("images", exist_ok=True)
        cv2.imwrite(os.path.join("images", filename + ".png"), image)

        trade_levels = get_levels(trade_data=trade_data, image=image)
        if trade_levels is False:
            df.to_csv("backtest_results.csv", index=False)
            shutdown()

        print(trade_levels)
        json_obj = clean_ai_response(trade_levels)
        print("\n")
        print(json_obj)

        trade_levels = json.loads(json_obj)

        # Write results back into the DataFrame
        df.at[idx, "ai_pair"] = trade_levels.get("pair", None)
        df.at[idx, "entry_price"] = trade_levels.get("entry_price", None)
        df.at[idx, "sl_price"] = trade_levels.get("sl_price", None)
        df.at[idx, "tp_price"] = trade_levels.get("tp_price", None)
        df.at[idx, "filename"] = filename

    except Exception as e:
        print(e)
        traceback.print_exc()

df.to_csv("backtest_results.csv", index=False)

