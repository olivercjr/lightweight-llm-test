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
	chat_history = f"<|assistant|>\n{greeting}<|assistant_end|>"


	# Ask questions
	while True:
		user_msg = input(f"\n{os.getenv("USER_NAME")}: ")
		if user_msg == "/stop": break
		else: chat_history += (f"\n<|user|>\n{user_msg}<|user_end|>\n<|assistant|>\n")
		print("--------------")
		
		# Chat formatting
		system_prompt = os.getenv("SYSTEM_PROMPT")
		full_prompt = f"<|system|>\n{system_prompt}<|system_end|>\n{chat_history}"
		response = llm(prompt=full_prompt, max_tokens=200, stop=["<|assistant_end|>", "<|user_end|>", "<|system_end|>"],temperature=0.6)
		# response = llm(prompt=full_prompt, max_tokens=200, temperature=0.6)
		response_str = response['choices'][0]['text']
		chat_history += f"{response_str}<|assistant_end|>"

		# Print the model's response
		print(f"\n{os.getenv("BOT_NAME")}: {response_str}")

	# end program
	print("\n---CHAT ENDS HERE---")
	print(f"<|system|>\n{system_prompt}<|system_end|>\n{chat_history}")



def input_test():
	user_msg = input(f"\n{os.getenv("USER_NAME")}: ")
	print(user_msg)






if __name__ == "__main__":
	chatbot()