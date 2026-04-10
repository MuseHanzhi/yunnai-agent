import json
import re

def extract_json(text):
    try:
        return json.loads(text)
    except:
        pass
        
    pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(pattern, text)
        
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
    except:
        pass

    raise ValueError("解析失败")