import os

def load_prompt(prompt_name):
    """
    Load a prompt template from the prompts folder
    
    Args:
        prompt_name (str): Name of the prompt file without .txt extension
        
    Returns:
        str: The prompt template content
    """
    try:
        prompt_path = os.path.join("prompts", f"{prompt_name}.txt")
        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file '{prompt_name}.txt' not found in prompts folder")
    except Exception as e:
        raise Exception(f"Error loading prompt '{prompt_name}': {str(e)}")

def get_subject_prompt(Title, Category):
    """Load and format the subject prompt template"""
    template = load_prompt("get_subject_prompt")
    return template.format(Title=Title, Category=Category)

def classify(cleanMessage):
    """Load and format the classification prompt template"""
    template = load_prompt("classify_prompt")
    return template.format(cleanMessage=cleanMessage)

def generate_interested_reply(reply_text):
    """Load and format the interested reply prompt template"""
    template = load_prompt("generate_interested_reply_prompt")
    return template.format(reply_text=reply_text)

def generate_not_interested_reply(reply_text):
    """Load and format the not interested reply prompt template"""
    template = load_prompt("generate_not_interested_reply_prompt")
    return template.format(reply_text=reply_text)

def generate_followup_prompt(Title, Category, Website):
    """Load and format the follow-up prompt template"""
    template = load_prompt("generate_followup_prompt")
    return template.format(Title=Title, Category=Category, Website=Website) 