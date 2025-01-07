
from helpers import parse_html_to_dict
from helpers import download_image,encode_image_to_base64,llm_call_with_image
from prompts import get_query_classification_prompt
import json


class QueryRouter: 
    def __init__(self,query):
        self.query = query
        self.query_text = ""
        self.query_imgs = ""
        self.updated_query_context = ""
    
    def parse_query(self):
        text, imgs = parse_html_to_dict(self.query)
        image_strings = []
        
        for img in imgs:
            image_path = download_image(img)
            image_base64,image_format = encode_image_to_base64(image_path)
            image_strings.append({"extension": image_format,"content": image_base64})
        self.query_text  = text
        self.query_imgs = image_strings

    
    def classify_query(self):
        self.parse_query()
        result = llm_call_with_image(get_query_classification_prompt(),self.query_text,self.query_imgs)
        print(result)
        res_json = json.loads(result.replace("```json","").replace("```",""))
        if "error_description" in res_json and res_json['error_description'] != "":
            self.updated_query_context = f"Query Summary:  {res_json['user_query_summary']}, Error Description: {res_json['error_description']}"
        else :
            self.updated_query_context = f"Query Summary:  {res_json['user_query_summary']}"
        return res_json['query_category']



# if __name__ == "__main__": 
#     user_query = """<p><img src="https://nkb-backend-ccbp-media-static.s3.ap-south-1.amazonaws.com/ccbp_prod/media/discussion_attachment/26715292-a21d-427d-bbcc-b334b0b0e2b2.jpeg"></p><p><img src="https://nkb-backend-ccbp-media-static.s3.ap-south-1.amazonaws.com/ccbp_prod/media/discussion_attachment/31cf48ae-6f74-48e3-b7f3-058147e6bd58.jpeg"></p><p><img src="https://nkb-backend-ccbp-media-static.s3.ap-south-1.amazonaws.com/ccbp_prod/media/discussion_attachment/9bfbad29-8c5c-4a41-b951-75c4e193031f.jpeg"></p><p><img src="https://nkb-backend-ccbp-media-static.s3.ap-south-1.amazonaws.com/ccbp_prod/media/discussion_attachment/2fb802a9-df00-420c-a705-c3874c62057f.jpeg"></p><p><br></p><p><br></p><p>explain me error and give me correct code </p>"""
#     router = QueryRouter(query=user_query) 
#     context = router.parse_query()
#     query_category = router.classify_query()
#     print(query_category)