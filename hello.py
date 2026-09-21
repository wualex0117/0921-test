import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

def calculate_bmi(height_cm, weight_kg):
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "體重過輕 (Underweight)"
    elif bmi < 24:
        return "正常範圍 (Normal)"
    elif bmi < 27:
        return "過重 (Overweight)"
    elif bmi < 30:
        return "輕度肥胖 (Mild obesity)"
    elif bmi < 35:
        return "中度肥胖 (Moderate obesity)"
    else:
        return "重度肥胖 (Severe obesity)"

def main():
    print("=== BMI 計算器 ===")
    try:
        height_cm = float(input("請輸入身高 (公分 cm): "))
        weight_kg = float(input("請輸入體重 (公斤 kg): "))
        
        if height_cm <= 0 or weight_kg <= 0:
            print("身高和體重必須大於 0！")
            return
        
        bmi = calculate_bmi(height_cm, weight_kg)
        category = get_bmi_category(bmi)
        
        print(f"\n你的 BMI 值為: {bmi:.2f}")
        print(f"健康狀態評估: {category}")
    except ValueError:
        print("輸入錯誤，請輸入有效的數字！")

if __name__ == "__main__":
    main()
