import re
import json
import traceback
from helpers import parse_html_to_dict
from helpers import download_image, encode_image_to_base64, llm_call_with_image
from prompts import get_query_classification_prompt
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class QueryRouter:
    def __init__(self, user_query, question_id, zip_path, question_content, question_test_cases):
        self.query = user_query
        self.question_command_id = question_id
        self.zip_path = zip_path
        self.question_content = question_content
        self.question_test_cases = question_test_cases

    def parse_query(self):
        text, imgs = parse_html_to_dict(self.query)
        image_strings = []

        for img in imgs:
            image_path = download_image(img)
            image_base64, image_format = encode_image_to_base64(image_path)
            image_strings.append({"extension": image_format, "content": image_base64})
        self.query_text = text
        self.query_imgs = image_strings

    def classify_query(self):
        self.parse_query()
        result = llm_call_with_image(get_query_classification_prompt(),self.query_text,self.query_imgs)
        logging.info(result)
        valid_json = result.replace("\\boxed{", "").replace("}", "")

        # Remove Markdown code block syntax (```json and ```)
        valid_json = valid_json.replace("```json", "").replace("```", "")
        res_json = json.loads(valid_json)
        logging.info(res_json)
        if "error_description" in res_json and res_json['error_description'] != "":
            self.updated_query_context = f"Query Summary:  {res_json['user_query_summary']}, Error Description: {res_json['error_description']}"
        else :
            self.updated_query_context = f"Query Summary:  {res_json['user_query_summary']}"
        return res_json['query_category']
