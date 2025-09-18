import pandas as pd
from gemini import get_levels,clean_ai_response
from utils import get_frame
import uuid
import cv2
import os
import json
import traceback


# df = pd.read_csv("trades.csv")

# selected_traders = ["Dee", "Aaron", "Jay", "Dakota", "Marie"]
# df = df[(df["trader"].isin(selected_traders))].copy()
# df = df.drop(columns=["time","time_s","yt_link","frame_number","yt_link","stream_time"])
# print(df.columns)
# print("len: ",len(df))
# df.to_csv("filtered_trades.csv",index=False)

# import pandas as pd

# def clean_trades(df):


#     # Get all links where there's an "opened" trade
#     opened_links = set(df.loc[df["trade_type"] == "opened", "link"])

#     # Keep rows that are:
#     #   - not recalculate_sl / update_tp, OR
#     #   - recalculate_sl / update_tp but the link has no "opened"
#     mask = ~df["trade_type"].isin(["recalculate_sl", "update_tp"]) | ~df["link"].isin(opened_links)
#     df_cleaned = df[mask]

#     # Save result
#     df_cleaned.to_csv("filtered_trades.csv", index=False)
#     return df_cleaned


df = pd.read_csv("filtered_trades.csv")
# print("we have : ",len(df)," trades")
# df = clean_trades(df)
# print("we have : ",len(df)," trades")


# Make sure df has the new columns first
df["ai_pair"] = None
df["entry_price"] = None
df["sl_price"] = None
df["tp_price"] = None
df["filename"] = None   # optional, if you want to keep the frame path

for idx, row in df.iterrows():
    try:
        trade_type = row["trade_action"]
        sl = row["sl"]
        tp = row["tp"]
        status = row["status"]

        trade_data = {"trade_type": trade_type, "status": status, "sl": sl, "tp": tp}

        # Get frame (assume your get_frame returns a path to saved image)
        image = get_frame(row["link"],cookies_file="b159.txt")
        filename = f"{uuid.uuid4().hex}"
        os.makedirs("images", exist_ok=True)
        cv2.imwrite(os.path.join("images",filename+".png"), image)
        

        # Get AI levels (you had a typo: pass trade_data, not trade_type)
        trade_levels = get_levels(trade_data=trade_data,image=image)
        print(trade_levels)
        json_obj = clean_ai_response(trade_levels)
        print("\n")
        print(json_obj)
        # pair_name = json.loads(json_obj)["pair_name"]
        # print(trade_levels)
        trade_levels = json.loads(json_obj)

        # Write results back into the DataFrame
        df.at[idx, "ai_pair"] = trade_levels.get("pair",None)
        df.at[idx, "entry_price"] = trade_levels.get("entry_price",None)
        df.at[idx, "sl_price"] = trade_levels.get("sl_price",None)
        df.at[idx, "tp_price"] = trade_levels.get("tp_price",None)
        df.at[idx, "filename"] = filename
    except Exception as e:
        print(e)
        
        traceback.print_exc()
df.to_csv("backtest_results.csv", index=False)
    
