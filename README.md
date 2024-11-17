== ChatZim ==

I've long made use of the Zim Desktop Wiki (https://zim-wiki.org/) for making notes about the tabletop roleplaying campaigns I run, and just generally for many other purposes.

With the advent of large language models I've been wanting to have some way to pull those notes into the context of an LLM in a convenient way. Zim's got a plugin system and I did a bit of poking around in it, but it turned out to be more convenient for me to create a stand-alone Python app. This is that app. I may turn it into a Zim plugin some other time, but for now this is working well for me.

In a nutshell; this application uses the OpenAI API to communicate with a large language model. Any OpenAI-compatible LLM will work, you don't strictly need an OpenAI account. Personally, I use KoboldCPP (https://github.com/LostRuins/koboldcpp) running the Command-R model (https://huggingface.co/bartowski/c4ai-command-r-08-2024-GGUF) running locally on my own computer. You point the application at an existing Zim wiki with the "Select Pages" command, then "Load Notebook" to navigate to the notebook.zim file in the root of your Zim wiki, and then from the resulting list of Zim pages you select which ones will be included in the system message as context for your conversation with the LLM. A rough word count is provided to give an approximate idea of how many tokens will be consumed, though bear in mind that there isn't a one-to-one correspondence between words and tokens. The content of the pages selected will be inserted into the system message after the text of the system prompt (which you can edit in the configuration settings).

Once the pages are loaded into context, you can chat with the LLM by typing into the text box at the bottom. You can change the selected pages at any point in the conversation if you want to switch what information the LLM has available to it.

If you're using a local LLM in the same manner I am, most of the configuration settings are likely not relevant and can be left blank. You don't need an API key for using local LLMs. I haven't actually tried this with an official OpenAI API so I can't make any promises about how well it'll actually work, I just implemented the headers I saw in their documentation and hoped I got it right.

This isn't really a clean "release" of this application, frankly. I'm just putting it out there in case anyone else wants to putter with something like this. No warranties!