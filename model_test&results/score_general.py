import json
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import time

API_KEY = "sk-a0215bc8713b46148c56ebfc080c81d8" 
BASE_URL = "https://api.deepseek.com"
JUDGE_MODEL = "deepseek-chat" # DeepSeek V3


# 三个模型对比
FILES = {
    "Base": "base_results.json",
    "Old_QA": "old_results.json",
    "LoRA_Mixed": "lora_results.json"
}
OUTPUT_EXCEL = "general_ability_report.xlsx"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def evaluate_general(question, reference, model_name, answer):
    prompt = f"""
    你是一个综合能力评估专家。
    
    【题目】: {question}
    【参考】: {reference}
    【考生({model_name})回答】: {answer}

    请打分（0-10分）。重点考察逻辑是否清晰、代码是否正确、语言是否流畅。
    如果是编程题，代码错误直接低分。
    如果是逻辑题，推理混乱直接低分。

    输出JSON: {{"score": <数字>, "reason": "<简评>"}}
    """
    for _ in range(3):
        try:
            resp = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        except:
            time.sleep(1)
    return {"score": 0, "reason": "Error"}

def main():
    datasets = {k: json.load(open(v, 'r', encoding='utf-8')) for k, v in FILES.items()}
    base_list = list(datasets.values())[0]
    records = []

    print(f"开始评估通用能力...")
    for i in tqdm(range(len(base_list))):
        item = base_list[i]
        row = {"Question": item['instruction'], "Category": item['category']}
        
        for name in FILES.keys():
            pred = datasets[name][i]['model_prediction']
            eval_res = evaluate_general(item['instruction'], item['reference'], name, pred)
            
            row[f"{name}_Answer"] = pred
            row[f"{name}_Score"] = eval_res['score']
        
        records.append(row)

    df = pd.DataFrame(records)
    print("\n=== 平均分统计 ===")
    for name in FILES.keys():
        print(f"{name}: {df[f'{name}_Score'].mean():.2f}")
        
    df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"报告已保存: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    main()