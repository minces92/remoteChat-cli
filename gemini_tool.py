import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python gemini_tool.py <prompt> [--model <model_name>]")
        sys.exit(1)

    prompt = sys.argv[1]
    model_name = "gemini-1.5-flash"
    
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model_name = sys.argv[idx + 1]

    # 모델 이름 매핑 (프론트엔드에서 전달되는 이름과 API에서 사용하는 이름이 다를 수 있음)
    model_mapping = {
        "gemini-3-flash-preview": "gemini-1.5-flash", # 임시 매핑 (실제 모델명에 맞게 수정 필요)
        "gemini-3-pro-preview": "gemini-1.5-pro",
        "gemini-2.5-pro": "gemini-1.5-pro",
        "gemini-2.5-flash": "gemini-1.5-flash",
        "gemini-2.5-flash-lite": "gemini-1.5-flash"
    }
    
    actual_model_name = model_mapping.get(model_name, model_name)

    # API 키 확인
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # GOOGLE_API_KEY가 없으면 GEMINI_API_KEY 확인
        api_key = os.getenv("GEMINI_API_KEY")
        
    if not api_key:
        print("Error: GOOGLE_API_KEY or GEMINI_API_KEY not found in .env file.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel(actual_model_name)
        response = model.generate_content(prompt)
        if response.text:
            print(response.text)
        else:
            print("Error: Empty response from Gemini API.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
