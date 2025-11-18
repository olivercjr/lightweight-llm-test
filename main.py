from llama_cpp import Llama
from dotenv import load_dotenv
import os

load_dotenv()


def chatbot():
	# Load the model (update the path!)
	llm = Llama(model_path=os.getenv("MODEL_PATH"), n_ctx=4096)
	print("\n---CHAT STARTS HERE---")
	greeting = os.getenv("GREETING")
	print(f"{os.getenv("BOT_NAME")}: {greeting}")
	chat_history = f"\n<start_of_turn>model\n{greeting}\n<end_of_turn>\n"
	pretty_chat = f"Assistant: {greeting}"


	# Ask questions
	while True:
		user_msg = input(f"\n{os.getenv("USER_NAME")}: ")
		if user_msg == "/stop": break
		else:
			chat_history += (f"\n<start_of_turn>user\n{user_msg}\n<end_of_turn>\n\n<start_of_turn>model\n")
			pretty_chat += f"\nUser: {user_msg}"
		print("--------------")
		
		# Gemma 3 Chat formatting
		system_prompt = os.getenv("SYSTEM_PROMPT")
		full_prompt = f"<start_of_turn>system\n{system_prompt}\n<end_of_turn>\n{chat_history}"
		response = llm(prompt=full_prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=0.6)
		response_str = response['choices'][0]['text']
		chat_history += f"{response_str}\n<end_of_turn>\n" #
		pretty_chat += f"\nAssistant: {response_str}"

		# Print the model's response
		print(f"\n{os.getenv("BOT_NAME")}: {response_str}")

	# end program
	print("\n---CHAT ENDS HERE---")
	# print(f"###SYSTEM PROMPT###\n{system_prompt}\n###########\n{pretty_chat}")
	print(full_prompt)



def input_test():
	user_msg = input(f"\n{os.getenv("USER_NAME")}: ")
	print(user_msg)






if __name__ == "__main__":
	chatbot()