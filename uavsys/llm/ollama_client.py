import ollama
from ollama import Client
from ..config import Config
from ..utils.richlog import RichLog, console

class OllamaClient:
    def __init__(self, config: Config):
        self.host = config.OLLAMA_HOST
        self.chat_model = config.CHAT_MODEL
        self.embed_model = config.EMBED_MODEL
        self.seed = getattr(config, "SEED", 0)
        self.client = Client(host=self.host)

    async def chat(self, messages: list[dict], temperature: float = 0.0, **kwargs) -> str:
        """
        Chats with the model and streams output to the Rich console.
        Returns the full response string.
        """
        
        full_response = ""
        try:
            if self.chat_model == "gpt-4o":
                from openai import AsyncOpenAI
                import os
                client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=1024
                )
                return response.choices[0].message.content
                
            if self.chat_model.startswith("claude-"):
                from anthropic import AsyncAnthropic, APIStatusError
                import os, asyncio
                client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
                
                # Anthropic API separates system prompt from messages array
                system_prompt = next((msg["content"] for msg in messages if msg["role"] == "system"), "")
                user_messages = [msg for msg in messages if msg["role"] != "system"]
                
                # Retry with exponential backoff for 529 Overloaded errors
                for attempt in range(5):
                    try:
                        response = await client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=1024,
                            temperature=temperature,
                            system=system_prompt,
                            messages=user_messages
                        )
                        return response.content[0].text
                    except APIStatusError as e:
                        if e.status_code == 529:
                            wait = 15 * (2 ** attempt)
                            RichLog.error("Claude", f"Overloaded (529). Retrying in {wait}s... (attempt {attempt+1}/5)")
                            await asyncio.sleep(wait)
                        else:
                            raise
                raise RuntimeError("Claude API still overloaded after 5 retries.")
                
            # Ollama execution
            
            from ollama import AsyncClient
            aclient = AsyncClient(host=self.host)
            
            # Options
            options = {
                "temperature": temperature,
                "seed": self.seed
            }

            stream = await aclient.chat(
                model=self.chat_model,
                messages=messages,
                options=options,
                stream=True,
                **kwargs
            )
            
            
            async for chunk in stream:
                content = chunk['message']['content']
                full_response += content
            
            return full_response

        except Exception as e:
            RichLog.error("Ollama", f"Chat failed: {e}")
            raise

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
             # ollama.embed returns {'embeddings': [[...], ...]}
             from ollama import AsyncClient
             aclient = AsyncClient(host=self.host)
             
             resp = await aclient.embed(model=self.embed_model, input=texts)
             return resp['embeddings']
        except Exception as e:
            RichLog.error("Ollama", f"Embedding failed: {e}")
            raise
