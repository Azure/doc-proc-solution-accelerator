import logging
import os
import json
import tiktoken
import time
from openai import AzureOpenAI, RateLimitError
from azure.identity import ManagedIdentityCredential, AzureCliCredential, ChainedTokenCredential, get_bearer_token_provider
from configuration import Configuration

MAX_RETRIES = 10 # Maximum number of retries for rate limit errors
MAX_EMBEDDINGS_MODEL_INPUT_TOKENS = 8192
MAX_GPT_MODEL_INPUT_TOKENS = 128000 # this is gpt4o max input, if using gpt35turbo use 16385

class AzureOpenAIConnector:
    """
    AzureOpenAIConnector uses the OpenAI SDK's built-in retry mechanism with exponential backoff.
    The number of retries is controlled by the MAX_RETRIES environment variable.
    Delays between retries start at 0.5 seconds, doubling up to 8 seconds.
    If a rate limit error occurs after retries, the client will retry once more after the retry-after-ms header duration (if the header is present).
    """
    def __init__(self, config : Configuration=None, settings : dict = {}):
        """
        Initializes the AzureOpenAI client.

        """     
        self.config = config
        self.settings = settings

        self.openai_service_name = self.config.get_value('AZURE_OPENAI_RESOURCE')
        self.openai_api_base = f"https://{self.openai_service_name}.openai.azure.com"
        self.openai_api_version = self.config.get_value('AZURE_OPENAI_API_VERSION')

        #check if the model is configured
        self.temperature = self.settings.get("temperature", self.config.get_value('AZURE_OPENAI_TEMPERATURE', 0.7))
        self.top_p = self.settings.get("top_p", self.config.get_value('AZURE_OPENAI_TOP_P', 1.0))
        self.frequency_penalty = self.settings.get("frequency_penalty", self.config.get_value('AZURE_OPENAI_FREQUENCY_PENALTY', 0.0))
        self.presence_penalty = self.settings.get("presence_penalty", self.config.get_value('AZURE_OPENAI_PRESENCE_PENALTY', 0.0))
        self.stop = self.settings.get("stop", self.config.get_value('AZURE_OPENAI_STOP', None, allow_none=True))
        self.max_completion_tokens = self.settings.get("max_completion_tokens", self.config.get_value('AZURE_OPENAI_MAX_TOKENS', 10000, type=int))
        self.stream = self.settings.get("stream", self.config.get_value('AZURE_OPENAI_STREAM', False, type=bool))

        token_provider = get_bearer_token_provider(
            self.config.credential, 
            "https://cognitiveservices.azure.com/.default"
        )

        self.client = AzureOpenAI(
            api_version=self.openai_api_version,
            azure_endpoint=self.openai_api_base,
            azure_ad_token_provider=token_provider,
            max_retries=MAX_RETRIES
        )

    def get_completion_messages(self, messages, max_tokens=800, retry_after=True, settings: dict = {}):
        logging.info(f"[aoai] Getting completion for messages: {messages[:100]}")
        openai_deployment = self.config.get_value('AZURE_OPENAI_CHATGPT_DEPLOYMENT')

        # truncate messages if needed
        #messages = self._truncate_input(messages, MAX_GPT_MODEL_INPUT_TOKENS)

        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=openai_deployment,
                temperature=float(self.temperature),
                top_p=float(self.top_p),
                max_tokens=max_tokens
            )

            completion = response.choices[0].message.content

            return completion

        except RateLimitError as e:
            retry_after_ms = e.response.headers.get('retry-after-ms')
            if retry_after_ms:
                retry_after_ms = int(retry_after_ms)
                logging.info(f"[aoai] get_completion_messages: Reached rate limit, retrying after {retry_after_ms} ms")
                time.sleep(retry_after_ms / 1000)
                return self.get_completion_messages(messages, max_tokens, retry_after=False)
            else:
                logging.error(f"[aoai] get_completion_messages: Rate limit error occurred, no 'retry-after-ms' provided: {e}")
                raise

        except Exception as e:
            logging.error(f"[aoai] get_completion_messages: An unexpected error occurred: {e}")
            raise

    def get_completion(self, prompt, max_tokens=800, retry_after=True, settings: dict = {}):
        one_liner_prompt = prompt.replace('\n', ' ')
        logging.info(f"[aoai] Getting completion for prompt: {one_liner_prompt[:100]}")
        openai_deployment = self.config.get_value('AZURE_OPENAI_CHATGPT_DEPLOYMENT')

        # truncate prompt if needed
        prompt = self._truncate_input(prompt, MAX_GPT_MODEL_INPUT_TOKENS)

        try:
            input_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{prompt}"}
            ]

            response = self.get_completion_messages(
                messages=input_messages,
                max_tokens=max_tokens,
                retry_after=retry_after,
                settings=settings
            )

            return response

        except RateLimitError as e:
            retry_after_ms = e.response.headers.get('retry-after-ms')
            if retry_after_ms:
                retry_after_ms = int(retry_after_ms)
                logging.info(f"[aoai] get_completion: Reached rate limit, retrying after {retry_after_ms} ms")
                time.sleep(retry_after_ms / 1000)
                return self.get_completion(self, prompt, retry_after=False, max_tokens=self.max_completion_tokens)
            else:
                logging.error(f"[aoai] get_completion: Rate limit error occurred, no 'retry-after-ms' provided: {e}")
                raise

        except Exception as e:
            logging.error(f"[aoai] get_completion: An unexpected error occurred: {e}")
            raise

    def get_embeddings(self, text, retry_after=True):
        one_liner_text = text.replace('\n', ' ')
        logging.info(f"[aoai] Getting embeddings for text: {one_liner_text[:100]}")        
        openai_deployment = self.config.get_value('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')

        # summarize in case it is larger than the maximum input tokens
        num_tokens = GptTokenEstimator().estimate_tokens(text)
        if (num_tokens > MAX_EMBEDDINGS_MODEL_INPUT_TOKENS):
            prompt = f"Rewrite the text to be coherent and meaningful, reducing it to {MAX_EMBEDDINGS_MODEL_INPUT_TOKENS} tokens: {text}"
            text = self.get_completion(prompt, max_tokens=self.max_completion_tokens)
            logging.info(f"[aoai] get_embeddings: rewriting text to fit in {MAX_EMBEDDINGS_MODEL_INPUT_TOKENS} tokens")

        try:
            response = self.client.embeddings.create(
                input=text,
                model=openai_deployment
            )
            embeddings = response.data[0].embedding
            return embeddings
        
        except RateLimitError as e:
            retry_after_ms = e.response.headers.get('retry-after-ms')
            if retry_after_ms:
                retry_after_ms = int(retry_after_ms)
                logging.info(f"[aoai ]get_completion: Reached rate limit, retrying after {retry_after_ms} ms")
                time.sleep(retry_after_ms / 1000)
                return self.get_completion(self, prompt, retry_after=False, max_tokens=self.max_completion_tokens)
            else:
                logging.error(f"[aoai] get_completion: Rate limit error occurred, no 'retry-after-ms' provided: {e}")
                raise

        except Exception as e:
            logging.error(f"[aoai] get_embedding: An unexpected error occurred: {e}")
            raise

    def _truncate_input(self, text, max_tokens):
        input_tokens = GptTokenEstimator().estimate_tokens(json.dumps(text))
        if input_tokens > max_tokens:
            logging.info(f"[aoai] Input size {input_tokens} exceeded maximum token limit {max_tokens}, truncating...")
            step_size = 1  # Initial step size
            iteration = 0  # Iteration counter

            while GptTokenEstimator().estimate_tokens(text) > max_tokens:
                text = text[:-step_size]
                iteration += 1

                # Increase step size exponentially every 5 iterations
                if iteration % 5 == 0:
                    step_size = min(step_size * 2, 100)

        return text    

class GptTokenEstimator():
    GPT2_TOKENIZER = tiktoken.get_encoding("gpt2")

    def estimate_tokens(self, text: str) -> int:
        return len(self.GPT2_TOKENIZER.encode(text))
