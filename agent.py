from helpers import LLMChat
import json

import os

class Action:
    def __init__(self, action_input):
        self.action_input = action_input

    def read(self):
        try:
            with open(self.action_input['file_location'], 'r') as file:
                content = file.read()
            return content
        except FileNotFoundError:
            return f"Error: File '{self.action_input['file_location']}' not found."
        except PermissionError:
            return f"Error: Permission denied to read file '{self.action_input['file_location']}'."
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"

    def edit(self):
        try:
            with open(self.action_input['file_location'], 'w') as file:
                file.write(self.action_input['file_content'])
            return f"Successfully replaced content in '{self.action_input['file_location']}'."
        except FileNotFoundError:
            return f"Error: File '{self.action_input['file_location']}' not found."
        except PermissionError:
            return f"Error: Permission denied to edit file '{self.action_input['file_location']}'."
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"

    def add(self):
        try:
            if os.path.exists(self.action_input['file_location']):
                return f"Error: File '{self.action_input['file_location']}' already exists."
            with open(self.action_input['file_location'], 'w') as file:
                file.write(self.action_input['file_content'])
            return f"Successfully created new file '{self.action_input['file_location']}' with the provided content."
        except PermissionError:
            return f"Error: Permission denied to create file '{self.action_input['file_location']}'."
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"


class Agent:
    def __init__(self, task_desc,issue,repo_state,max_steps=10):
        self.chat = LLMChat(task_desc)
        self.issue  = issue
        self.repo_state = repo_state
        self.max_steps = max_steps
        self.scratchpad = []
    def _parse_agent_response(self,response):
        res_json = json.loads(response.replace("```json","").replace("```",""))
        thought = res_json["thought"]
        action = res_json['action']
        action_input = res_json['action_input']
        self.scratchpad.append(res_json)
        return thought,action,action_input
    def execute(self):
        steps = 0 
        user_prompt = f"Issue:{self.issue}, Repo Dir Tree: {self.repo_state}"
        while steps < self.max_steps:
            response = self.chat.llm_call(user_prompt)
            print(response)
            thought, action_to_take , action_input = self._parse_agent_response(response)
            action =  Action(action_input)
            if action_to_take == "<done>":
                return thought, action_input
            elif action_to_take == "<read>":
                user_prompt = f"Observation: {action.read()}"
            elif action_to_take == "<add>":
                user_prompt = f"Observation: {action.add()}"
            elif action_to_take == "<edit>":
                user_prompt = f"Observation: {action.edit()}" 
                print(user_prompt)       
            steps +=1


        
