import google.generativeai as genai
from PIL import Image
# from main import print
import os
import cv2
import re 
import json
# from mt5_functions import map_pairs
import subprocess

def build_trade_prompt(trade_data: list) -> tuple:
    """
    Builds a prompt for a vision model to extract trade data (pair name, entry price, SL, TP).
    SL and TP are included only if relevant to reduce token usage.
    """
    color_map = {"profit": "green", "loss": "red"}
    trade_descriptions = []
    instruction_items = []
    json_fields = {'pair': '<symbol>', 'entry_price': '<float>'}
    # trads =[]
    # trads = trads.append(trade_data)
    # trade_data = trads
    for i, trade in enumerate(trade_data, 1):
        desc = f"Trade {i}: Type = {trade['trade_type'].capitalize()}."

        if trade.get("sl"):
            desc += " This trade has a Stop Loss, which is usually shown as a red box with a negative value."
            instruction_items.append("The stop loss price (red box with negative value)")
            json_fields["sl_price"] = "<float>"

        if trade.get("tp"):
            desc += " This trade has a Take Profit, usually shown as a green box with a positive value."
            instruction_items.append("The take profit price (green box with positive value)")
            json_fields["tp_price"] = "<float>"

        status = trade.get("status", "profit")
        line_color = color_map.get(status, "green")
        desc += f" The Entry Price is typically shown as a horizontal {line_color} line since the trade is in {status}."

        trade_descriptions.append(desc)

    # Always required
    instruction_items = [
        "The instrument or pair name (e.g., MNQ, EURUSD)",
        "The entry price (look for the horizontal green or red line)",
    ] + instruction_items

    # Dynamically numbered instructions
    numbered_instructions = [f"{idx + 1}. {item}" for idx, item in enumerate(instruction_items)]
    instruction_block = "\n".join(["Please extract and return the following:"] + numbered_instructions)

    # Build final JSON template
    json_output = "{\n" + "\n".join([f'  "{k}": {v},' for k, v in json_fields.items()])[:-1] + "\n}"

    # Final prompt
    prompt = f"""
This is a screenshot from a trading platform.

{chr(10).join(trade_descriptions)}

{instruction_block}

Return the answer in this JSON format:

{json_output}

Incase of an error return JSON where all values are None.
""".strip()

    return  prompt



from PIL import Image
import numpy as np

def ndarray_to_pil(img_array):
    if img_array.dtype != np.uint8:
        img_array = img_array.astype(np.uint8)

    # If it's a grayscale image, convert mode to 'L'
    if len(img_array.shape) == 2:
        return Image.fromarray(img_array, mode='L')
    
    # If it's a color image, use 'RGB'
    elif len(img_array.shape) == 3:
        return Image.fromarray(img_array, mode='RGB')
    
    else:
        raise ValueError("Unsupported ndarray shape for image.")


API_KEY = "AIzaSyCrRumsDJLndwP3jQ9vxoY447Az3StMjmo"

def get_levels(image, trade_data):
    genai.configure(api_key=API_KEY)
    print("trade data in get levels")

    if not isinstance(trade_data, list):
        trade_data = [trade_data]

    prompt = build_trade_prompt(trade_data)

    model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')

    # Convert image to PIL if needed
    img = ndarray_to_pil(image)
    contents = [prompt, img]

    try:
        # Count tokens
        tokens_info = model.count_tokens(contents)
        print(f"🔢 Estimated tokens in request: {tokens_info.total_tokens}")

        # Send image and prompt together
        response = model.generate_content(
            [prompt, img],
            generation_config={"temperature": 0.3}
        )
        return response.text

    except Exception as e:
        error_msg = str(e).lower()
        print(f"⚠️ Error in get_levels: {e}")

        # Detect request/usage limits
        if "quota" in error_msg or "limit" in error_msg or "rate" in error_msg:
            print("🚨 Request limit reached — shutting down instance...")
            return False
        else:
            
            raise  # re-raise if it's another error
            

def unmap_pair(pair):
    if pair == "BTCUSD":
        img_name = "micro_gold"
    elif pair == "ETHUSD":
        img_name = "micro_crude_oil"
    elif pair == "LTCUSD":
        img_name = "micro_nasdaq"
    elif pair == "BCHUSD":
        img_name = "micro_spy_500"
    else :
        img_name =None
        print("Unmap pair did not find a suitable match for: ",pair,log_path="error.txt")
    
    img = cv2.imread(os.path.join(os.path.dirname(__file__), "pairs_2_resized", f"{img_name}.png"))
    return img

def clean_ai_response(trade_json):
    try:

        if trade_json.startswith("```"):
            trade_json = re.sub(r"^```[a-zA-Z0-9]*\s*", "", trade_json)  # remove opening ```
            trade_json = re.sub(r"\s*```$", "", trade_json)              # remove closing ```

        trade_json = trade_json.strip()

        return trade_json

    except json.JSONDecodeError as e:
        # Save raw text to json_error.txt
        json_error_file = os.path.join(os.path.dirname(__file__), "json_error.txt")
        with open(json_error_file, "a", encoding="utf-8") as f:
            f.write(trade_json + "\n\n")
        print(f"Error decoding JSON: {e}", log_path="errors.txt")
        return None



if __name__ == "__main__":
    # trades = [{'sl': True, 'tp': False, 'trade_type': 'buy' ,'status' : 'profit' }]
    # print(get_levels("file.png", trades))
    # Configure API key
    API_KEY = "AIzaSyCrRumsDJLndwP3jQ9vxoY447Az3StMjmo"
    genai.configure(api_key=API_KEY)

    # List available models
    models = genai.list_models()

    for model in models:
        print(model.name)